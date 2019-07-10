import unittest
from sqlalchemy.exc import IntegrityError

from alayatodo import app, db
from alayatodo.models import User, Todo


def login(client, username, password):
    return client.post('/login', data=dict(username=username, password=password), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def create_todo(client, description, user):
    return client.post('/todo/', data=dict(description=description, user_id=user.id), follow_redirects=True)


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
        user = User(username='test', password='test')
        db.session.add(user)
        db.session.commit()
        assert user in db.session
        with app.test_client() as c:
            response = login(c, user.username, user.password)
            assert b'Successful login' in response.data
            response = logout(c)
            assert b'You were logged out' in response.data
            invalid_login = b'Invalid username or password'
            response = login(c, 'invalid username', user.password)
            assert invalid_login in response.data
            response = login(c, user.username, 'invalid password')
            assert invalid_login in response.data

    def testUserCreation(self):
        """
        Ensures we can create a user, but not without username or password, or if username or password are empty
        """
        user = User(username='test', password='test')
        db.session.add(user)
        db.session.commit()
        assert user in db.session
        user = User(password='test')
        db.session.add(user)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        with self.assertRaises(AssertionError):
            User(password='test', username='')
        user = User(username='test')
        db.session.add(user)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        with self.assertRaises(AssertionError):
            User(password='', username='test')

    def testTodoCreation(self):
        """
        Ensures we can create a todo, but not if it has an empty description or empty user
        """
        user = User(username='test', password='test')
        db.session.add(user)
        todo = Todo(description='some desc', user=user)
        db.session.add(todo)
        db.session.commit()
        assert todo in db.session
        with self.assertRaises(AssertionError):
            Todo(description='', user=user)
        no_user_todo = Todo(description='some desc')
        db.session.add(no_user_todo)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def testViewTodoCreation(self):
        """
        Ensures we get correct responses from the server when creating todos
        """
        user = User(username='test', password='test')
        db.session.add(user)
        db.session.commit()
        assert user in db.session
        with app.test_client() as c:
            with c.session_transaction() as session:
                session['user_id'] = user.id
                response = create_todo(c, 'some desc', user)
                assert b'Todo was successfully created' in response.data
                response = create_todo(c, '', user)
                assert b'Todo description cannot be empty' in response.data


if __name__ == '__main__':
    unittest.main()
