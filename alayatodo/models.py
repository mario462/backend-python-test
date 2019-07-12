from alayatodo import db
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow_sqlalchemy import ModelSchema


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        assert password is not None
        assert len(password) > 0
        self.username = username
        self.set_password(password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @validates('username', 'password_hash')
    def validates_presence(self, _, field):
        assert field is not None, 'Neither username nor password can be None'
        assert len(field) > 0, 'Neither username nor password can be empty'
        return field

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, server_default='0')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Todo {}>'.format(self.description)

    def as_dict(self):
        todo_schema = TodoSchema()
        return todo_schema.dump(self).data

    @validates('description')
    def validates_presence(self, _, field):
        assert field is not None, 'Description cannot be None'
        assert len(field.strip()) > 0, 'Description cannot be empty'
        return field

    @validates('user')
    def validate_has_user(self, _, user):
        assert user is not None, 'Todo must belong to a user'
        return user


class TodoSchema(ModelSchema):
    class Meta:
        model = Todo
