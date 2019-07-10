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
    session.pop('username', None)
    session.pop('user_id', None)

    flash('You were logged out', 'danger')
    return redirect('/')


@app.route('/todo/<id>', methods=['GET'])
def todo(id):
    todo = Todo.query.get(id)
    return render_template('todo.html', todo=todo)


@app.route('/todo/', methods=['GET'])
def todos():
    if not session.get('user_id'):
        return redirect('/login')
    todos = Todo.query.all()
    return render_template('todos.html', todos=todos)


@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('user_id'):
        return redirect('/login')
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
def todo_delete(id):
    if not session.get('user_id'):
        return redirect('/login')
    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect('/todo')
