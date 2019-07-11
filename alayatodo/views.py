from alayatodo import app, db
from alayatodo.models import User, Todo
from sqlalchemy import and_
from flask import (
    redirect,
    render_template,
    request,
    session,
    flash
)
import functools


def require_login(function):
    """
    Decorator to ensure all routes that require a logged in user share the same functionality, implemented in a
    reusable manner. Ideally, for a real life application we would use a solution like flask_login
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page', 'danger')
            return redirect('/login')
        return function(*args, **kwargs)

    return wrapper


@app.route('/')
def home():
    with app.open_resource('../README.md', mode='r') as f:
        readme = "".join(l.decode('utf-8') for l in f)
        return render_template('index.html', readme=readme)


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_POST():
    username = request.form.get('username')
    password = request.form.get('password')

    user = db.session.query(User).filter(and_(User.username == username, User.password == password)).first()
    if user:
        session['username'] = user.username
        session['user_id'] = user.id
        flash('Successful login', 'success')
        return redirect('/todo')
    flash('Invalid username or password', 'danger')
    return redirect('/login')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        flash('You were logged out', 'danger')
    session.pop('username', None)
    session.pop('user_id', None)

    return redirect('/')


@app.route('/todo/<id>', methods=['GET'])
@require_login
def todo(id):
    todo = db.session.query(Todo).filter(Todo.id == id, Todo.user_id == session['user_id']).first_or_404()
    return render_template('todo.html', todo=todo)


@app.route('/todo/', methods=['GET'])
@require_login
def todos():
    todos = db.session.query(Todo).filter(Todo.user_id == session['user_id'])
    return render_template('todos.html', todos=todos)


@app.route('/todo/', methods=['POST'])
@require_login
def todos_POST():
    try:
        todo = Todo(description=request.form.get('description', ''), user_id=session['user_id'])
        db.session.add(todo)
        db.session.commit()
        flash('Todo was successfully created', 'success')
    except AssertionError:
        db.session.rollback()
        flash('Todo description cannot be empty', 'danger')
    return redirect('/todo')


@app.route('/todo/<id>', methods=['POST'])
@require_login
def todo_update(id):
    todo = db.session.query(Todo).filter(Todo.id == id, Todo.user_id == session['user_id']).first_or_404()
    if request.form.get('_method', '').upper() == 'DELETE':
        flash('Todo has been deleted.', 'danger')
        db.session.delete(todo)
    else:
        completed = request.form.get('completed') is not None
        todo.completed = completed
        flash('Todo has been marked as {}completed.'.format('' if
                                                            completed else 'not '), 'success')
        db.session.add(todo)
    db.session.commit()
    return redirect('/todo')
