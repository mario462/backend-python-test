import json
import unittest

from faker import Faker
from sqlalchemy.exc import IntegrityError

from alayatodo import app, db
from alayatodo.models import User, Todo

myFactory = Faker()


def db_commit(model):
    db.session.add(model)
    db.session.commit()


def create_random_user():
    # We need to return the plain text password used during user creation in order to call the login function later
    password = myFactory.word()
    return User(username=myFactory.first_name(), password=password), password


def create_random_todo(user):
    return Todo(description=myFactory.text(), user=user)


def login(client, username, password):
    return client.post('/login', data=dict(username=username, password=password), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def create_todo(client, description, user):
    return client.post('/todo/', data=dict(description=description, user_id=user.id), follow_redirects=True)


def get_todos(client):
    return client.get('/todo/', follow_redirects=True)


def get_todo(client, todo_id):
    return client.get('/todo/{}'.format(todo_id), follow_redirects=True)


def delete_todo(client, todo_id):
    return client.delete('/todo/{}'.format(todo_id), follow_redirects=True)


def update_completed_todo(client, todo_id, completed):
    return client.post('/todo/{}'.format(todo_id), data=dict(completed=completed), follow_redirects=True)


def json_todo(client, todo_id):
    return client.get('/todo/{}/json'.format(todo_id), follow_redirects=True)


def visit_login(client):
    return client.get('/login', follow_redirects=True)


def show_completed(client, show):
    return client.post('/show_completed', data=dict(show_completed=show), follow_redirects=True)


class AlayatodoTests(unittest.TestCase):
    def setUp(self):
        """
        Creates a new database for the unit test to use
        """
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['WTF_CSRF_METHODS'] = []
        db.create_all()

    def tearDown(self):
        """
        Ensures that the database is emptied for next unit test
        """
        db.session.remove()
        db.drop_all()

    def testLoginLogout(self):
        """
        Ensures a user can login if correct username and password are provided
        """
        user, password = create_random_user()
        db_commit(user)
        assert user in db.session
        with app.test_client() as c:
            response = login(c, user.username, password)
            assert 'Successful login' in response.data
            response = logout(c)
            assert 'You were logged out' in response.data
            invalid_login = 'Invalid username or password'
            response = login(c, '{}XXX'.format(user.username), password)
            assert invalid_login in response.data
            response = login(c, user.username, '{}XXX'.format(password))
            assert invalid_login in response.data

    def testUserCreation(self):
        """
        Ensures we can create a user, but not without username or password, or if username or password are empty
        """
        user, _ = create_random_user()
        db_commit(user)
        assert user in db.session
        with self.assertRaises(AssertionError):
            User(username=None, password=myFactory.word())
        with self.assertRaises(AssertionError):
            User(password=myFactory.word(), username='')
        with self.assertRaises(AssertionError):
            User(username=myFactory.first_name(), password=None)
        with self.assertRaises(AssertionError):
            User(password='', username=myFactory.first_name())
        with self.assertRaises(IntegrityError):
            same_username = User(username=user.username, password=myFactory.word())
            db.session.add(same_username)
            db.session.commit()

    def testTodoCreation(self):
        """
        Ensures we can create a todo, but not if it has an empty description or empty user
        """
        user, _ = create_random_user()
        db_commit(user)
        todo = create_random_todo(user)
        db_commit(todo)
        assert todo in db.session
        with self.assertRaises(AssertionError):
            Todo(description='', user=user)
        no_user_todo = Todo(description=myFactory.text())
        db.session.add(no_user_todo)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def testViewTodoCreation(self):
        """
        Ensures we get correct responses from the server when creating todos
        """
        user, password = create_random_user()
        db_commit(user)
        assert user in db.session
        with app.test_client() as c:
            login(c, user.username, password)
            response = create_todo(c, 'some desc', user)
            assert 'Todo was successfully created' in response.data
            response = create_todo(c, '', user)
            assert 'Todo description cannot be empty' in response.data

    def testPrivateTodos(self):
        """
        Ensures users can only see their todos and cannot access another user's todos by id
        """
        db.session.expire_on_commit = False
        user, password = create_random_user()
        db.session.add(user)
        other_user, other_password = create_random_user()
        db.session.add(other_user)
        todo = create_random_todo(user)
        db.session.add(todo)
        other_todo = create_random_todo(other_user)
        db.session.add(other_todo)
        db.session.commit()

        my_todo_id = todo.id
        my_todo_desc = todo.description
        other_todo_id = other_todo.id
        other_todo_desc = other_todo.description
        with app.test_client() as c:
            login(c, user.username, password)
            response = get_todos(c)
            assert my_todo_desc in response.data
            assert other_todo_desc not in response.data
            response = get_todo(c, my_todo_id)
            self.assertEqual(response.status, '200 OK')
            response = get_todo(c, other_todo_id)
            self.assertEqual(response.status, '404 NOT FOUND')
            response = delete_todo(c, my_todo_id)
            self.assertEqual(response.status, '200 OK')
            response = delete_todo(c, other_todo_id)
            self.assertEqual(response.status, '404 NOT FOUND')

    def testCompleteTodos(self):
        """
        Ensures a user can mark a todo as completed and reverse it
        """
        db.session.expire_on_commit = False
        user, password = create_random_user()
        db.session.add(user)
        todo = create_random_todo(user)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id
        with app.test_client() as c:
            login(c, user.username, password)
            response = update_completed_todo(c, todo_id, True)
            assert 'Todo has been marked as completed.' in response.data
            response = update_completed_todo(c, todo_id, None)
            assert 'Todo has been marked as not completed.' in response.data

    def testTodoJson(self):
        """
        Ensures a user can view a todo as JSON
        """
        db.session.expire_on_commit = False
        user, password = create_random_user()
        db.session.add(user)
        todo = create_random_todo(user)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id
        with app.test_client() as c:
            login(c, user.username, password)
            response = json_todo(c, todo_id)
            self.assertEqual(todo_id, json.loads(response.data)['todo']['id'])

    def testRedirectLoggedInUser(self):
        """
        Ensures a logged in user should be redirected to his todo list when trying to access the login page
        """
        user, password = create_random_user()
        db.session.add(user)
        db.session.commit()
        with app.test_client() as c:
            response = visit_login(c)
            assert 'Login' in response.data
            login(c, user.username, password)
            response = visit_login(c)
            assert 'Todo List' in response.data

    def testHideCompletedTodo(self):
        """
        Ensures completed todos are hidden if option selected
        """
        db.session.expire_on_commit = False
        user, password = create_random_user()
        db.session.add(user)
        db.session.commit()
        todo = create_random_todo(user)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id
        todo_desc = todo.description
        with app.test_client() as c:
            login(c, user.username, password)
            response = get_todos(c)
            assert todo_desc in response.data
            update_completed_todo(c, todo_id, True)
            response = get_todos(c)
            assert todo_desc not in response.data
            show_completed(c, True)
            response = get_todos(c)
            assert todo_desc in response.data

    def testDeleteTodo(self):
        db.session.expire_on_commit = False
        user, password = create_random_user()
        db.session.add(user)
        db.session.commit()
        todo = create_random_todo(user)
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id
        todo_desc = todo.description
        with app.test_client() as c:
            login(c, user.username, password)
            response = get_todos(c)
            assert todo_desc in response.data
            delete_todo(c, todo_id)
            response = get_todos(c)
            assert todo_desc not in response.data


if __name__ == '__main__':
    unittest.main()
