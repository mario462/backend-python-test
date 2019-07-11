from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# configuration
DATABASE = '/tmp/alayatodo.db'
DEBUG = True
SECRET_KEY = 'development key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False
FLASK_APP = 'alayatodo.py'
TODOS_PER_PAGE = 10

app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from alayatodo import views, models
