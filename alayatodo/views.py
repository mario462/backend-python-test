from alayatodo import app, db
from alayatodo.models import User, Todo
import json
from flask import (
    redirect,
    render_template,
    request,
    session,
    flash,
    jsonify,
    url_for,
    make_response
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
            return redirect(url_for('login'))
        return function(*args, **kwargs)

    return wrapper


@app.route('/')
def home():
    with app.open_resource('../README.md', mode='r') as f:
        readme = "".join(l.decode('utf-8') for l in f)
        return render_template('index.html', readme=readme)


@app.route('/login', methods=['GET'])
def login():
    if not session.get('user_id'):
        return render_template('login.html')
    return redirect(url_for('todos'))


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    session['username'] = user.username
    session['user_id'] = user.id
    flash('Successful login', 'success')
    return redirect(url_for('todos'))


@app.route('/logout')
def logout():
    if 'user_id' in session:
        flash('You were logged out', 'danger')
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/todo/<todo_id>', methods=['GET'])
@require_login
def todo(todo_id):
    todo = db.session.query(Todo).filter(Todo.id == todo_id, Todo.user_id == session['user_id']).first_or_404()
    return render_template('todo.html', todo=todo)


@app.route('/todo/', methods=['GET'])
@require_login
def todos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', app.config['TODOS_PER_PAGE'], type=int)
    show_completed_cookie = request.cookies.get('show_completed')
    user_showing = False
    user_id = session['user_id']
    if show_completed_cookie is not None:
        show_completed_cookie = json.loads(show_completed_cookie)
        user_showing = str(user_id) in show_completed_cookie
    todos = db.session.query(Todo).filter(Todo.user_id == user_id).order_by(Todo.completed.asc(), Todo.id.desc())
    if not user_showing:
        todos = todos.filter(Todo.completed != True)
    todos = todos.paginate(page, per_page, False)
    return render_template('todos.html', todos=todos, per_page=per_page, show_completed=user_showing)


@app.route('/todo/', methods=['POST'])
@require_login
def todos_post():
    try:
        todo = Todo(description=request.form.get('description', ''), user_id=session['user_id'])
        db.session.add(todo)
        db.session.commit()
        flash('Todo was successfully created', 'success')
    except AssertionError:
        db.session.rollback()
        flash('Todo description cannot be empty', 'danger')
    return redirect(url_for('todos'))


@app.route('/todo/<todo_id>', methods=['POST'])
@require_login
def todo_update(todo_id):
    todo = db.session.query(Todo).filter(Todo.id == todo_id, Todo.user_id == session['user_id']).first_or_404()
    if request.form.get('_method', '').upper() == 'DELETE':
        flash('Todo has been deleted.', 'danger')
        db.session.delete(todo)
    else:
        completed = request.form.get('completed') is not None
        todo.completed = completed
        flash('Todo has been marked as {}completed.'.format('' if completed else 'not '), 'success')
        db.session.add(todo)
    db.session.commit()
    return redirect(url_for('todos'))


@app.route('/todo/<todo_id>/json', methods=['GET'])
def todo_json(todo_id):
    status = 200
    message = 'Success'
    data = {}
    if not session.get('user_id'):
        status = 401
        message = 'Please login to access this page.'
    else:
        todo = db.session.query(Todo).filter(Todo.id == todo_id, Todo.user_id == session['user_id']).first()
        if todo is None:
            status = 404
            message = 'File not found.'
        else:
            data = todo.as_dict()
    return jsonify({'status': status, 'message': message, 'todo': data}), status


@app.route('/show_completed', methods=['POST'])
@require_login
def show_completed():
    show = request.form.get('show_completed') is not None
    flash('{} completed todos.'.format('Showing' if show else 'Hiding'), 'success')
    resp = make_response(redirect(url_for('todos')))
    showing = {}
    cookie = request.cookies.get('show_completed')
    if cookie is not None:
        showing = json.loads(cookie)
    user_id = str(session['user_id'])
    if show and user_id not in showing:
        showing[user_id] = 'True'
    else:
        showing.pop(user_id)
    resp.set_cookie('show_completed', json.dumps(showing))
    return resp
