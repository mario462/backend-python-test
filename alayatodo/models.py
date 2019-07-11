from alayatodo import db
from sqlalchemy.orm import validates


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @validates('username', 'password')
    def validates_presence(self, _, field):
        assert field is not None, 'Neither username nor password can be None'
        assert len(field) > 0, 'Neither username nor password can be empty'
        return field


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, server_default='0')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Todo {}>'.format(self.description)

    @validates('description')
    def validates_presence(self, _, field):
        assert field is not None, 'Description cannot be None'
        assert len(field) > 0, 'Description cannot be empty'
        return field

    @validates('user')
    def validate_has_user(self, _, user):
        assert user is not None, 'Todo must belong to a user'
        return user
