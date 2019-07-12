from flask_migrate import upgrade
from alayatodo import app


def upgradedb():
    with app.app_context():
        upgrade()


if __name__ == '__main__':
    upgradedb()
