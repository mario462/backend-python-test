import unittest
from sqlalchemy.exc import IntegrityError
from faker import Faker

from alayatodo import app, db
from alayatodo.models import User, Todo

myFactory = Faker()


def dbCommit(object):
    db.session.add(object)
    db.session.commit()


def createRandomUser():
    return User(username=myFactory.first_name(), password=myFactory.word())


def createRandomTodo(user):
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
    return client.post('/todo/{}'.format(todo_id), follow_redirects=True)


class AlayatodoTests(unittest.TestCase):
    def setUp(self):
        """
        Creates a new database for the unit test to use
        """
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
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
        user = createRandomUser()
        dbCommit(user)
        assert user in db.session
        with app.test_client() as c:
            response = login(c, user.username, user.password)
            assert b'Successful login' in response.data
            response = logout(c)
            assert b'You were logged out' in response.data
            invalid_login = b'Invalid username or password'
            response = login(c, '{}XXX'.format(user.username), user.password)
            assert invalid_login in response.data
            response = login(c, user.username, '{}XXX'.format(user.password))
            assert invalid_login in response.data

    def testUserCreation(self):
        """
        Ensures we can create a user, but not without username or password, or if username or password are empty
        """
        user = createRandomUser()
        dbCommit(user)
        assert user in db.session
        user = User(password=myFactory.word())
        db.session.add(user)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        with self.assertRaises(AssertionError):
            User(password=myFactory.word(), username='')
        user = User(username=myFactory.word())
        db.session.add(user)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        with self.assertRaises(AssertionError):
            User(password='', username=myFactory.word())

    def testTodoCreation(self):
        """
        Ensures we can create a todo, but not if it has an empty description or empty user
        """
        user = createRandomUser()
        dbCommit(user)
        todo = createRandomTodo(user)
        dbCommit(todo)
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
        user = createRandomUser()
        dbCommit(user)
        assert user in db.session
        with app.test_client() as c:
            login(c, user.username, user.password)
            response = create_todo(c, 'some desc', user)
            assert b'Todo was successfully created' in response.data
            response = create_todo(c, '', user)
            assert b'Todo description cannot be empty' in response.data

    def testPrivateTodos(self):
        """
        Ensures users can only see their todos and cannot access another user's todos by id
        """
        db.session.expire_on_commit = False
        user = createRandomUser()
        db.session.add(user)
        other_user = createRandomUser()
        db.session.add(other_user)
        todo = createRandomTodo(user)
        db.session.add(todo)
        other_todo = createRandomTodo(other_user)
        db.session.add(other_todo)
        db.session.commit()

        my_todo_id = todo.id
        my_todo_desc = todo.description
        other_todo_id = other_todo.id
        other_todo_desc = other_todo.description
        with app.test_client() as c:
            login(c, user.username, user.password)
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


if __name__ == '__main__':
    unittest.main()
