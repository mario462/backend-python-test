"""AlayaNotes

Usage:
  main.py [run]
  main.py initdb
"""
from docopt import docopt
import os
import json
import subprocess

from alayatodo import app, db, models, FLASK_APP


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
            db.session.commit()
    except IOError:
        print('Seeds file not found, make sure {} exists.'.format(file))


if __name__ == '__main__':
    args = docopt(__doc__)
    flask_app_variable = 'FLASK_APP'
    # flask db commands rely on FLASK_APP environment variable to be set.
    # Ideally, we would use something like dotenv to set this
    if flask_app_variable not in os.environ:
        os.environ[flask_app_variable] = FLASK_APP
    seeds_file_path = 'resources/seeds.json'
    # Using subprocess to call external flask database manipulation commands.
    if args['initdb']:
        db_init_command = ['flask', 'db', 'init']
        print('Initializing database. Calling ${}'.format(' '.join(db_init_command)))
        subprocess.call(db_init_command)
        db_upgrade_command = ['flask', 'db', 'upgrade']
        print('Running pending migrations. Calling ${}'.format(' '.join(db_upgrade_command)))
        subprocess.call(db_upgrade_command)
        print('Seeding database with initial values. You can find initial values in {}'.format(seeds_file_path))
        seed(seeds_file_path)
        print('All done, database initialized.')
    else:
        app.run(use_reloader=True)
