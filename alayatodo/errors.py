from flask import render_template
from flask_wtf.csrf import CSRFError

from alayatodo import app, db


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    return render_template('csrf_error.html', reason=error.description), 400
