"""AlayaNotes

Usage:
  main.py [run]
  main.py initdb
"""
from docopt import docopt
import json
from flask_migrate import upgrade
from sqlalchemy.exc import IntegrityError

from alayatodo import app, db, models


def seed(path):
    try:
        with open(path) as seeds_file:
            users = json.load(seeds_file)
            for user in users:
                new_user = models.User(username=user['username'], password=user['password'])
                db.session.add(new_user)
                for todo in user['todos']:
                    new_todo = models.Todo(description=todo['description'], user=new_user)
                    db.session.add(new_todo)
            try:
                db.session.commit()
            except IntegrityError:
                print(
                    'WARNING: Database was already initialized. Make sure you delete {} before running initdb.'.format(
                        app.config['DATABASE']))
                db.session.rollback()
    except IOError:
        print('Seeds file not found, make sure {} exists.'.format(path))


if __name__ == '__main__':
    args = docopt(__doc__)
    seeds_file_path = 'resources/seeds.json'
    if args['initdb']:
        with app.app_context():
            print('Initializing database.')
            print('Running pending migrations with $flask db upgrade')
            upgrade()
            print('Seeding database with initial values. You can find initial values in {}'.format(seeds_file_path))
            seed(seeds_file_path)
            print('All done, database initialized.')
    else:
        app.run(use_reloader=True)
