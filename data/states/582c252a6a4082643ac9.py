from __future__ import annotations

import sqlite3, hashlib
from flask import Flask, request, session, redirect, url_for, g, render_template_string

DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(q, args=(), one=False):
    cur = get_db().execute(q, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    db.commit()

def add_user(username: str, password: str):
    assert username and password, "username and password required"
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, password) VALUES (?,?)',
                   (username, pw_hash))
        db.commit()
    except sqlite3.IntegrityError:
        pass

def create_app():
    app = Flask(__name__)
    app.secret_key = 'devkey'

    @app.before_request
    def before():
        g.user = None
        if 'user_id' in session:
            row = query_db('SELECT id, username FROM users WHERE id=?',
                           [session['user_id']], one=True)
            if row:
                g.user = {'id': row[0], 'username': row[1]}

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    @app.route('/')
    def index():
        if g.user:
            return f'Hello, {g.user["username"]}! <a href="/logout">Logout</a>'
        return 'You are not logged in. <a href="/login">Login</a>'

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            assert username and password, "Missing credentials"
            user = query_db('SELECT id, password FROM users WHERE username=?',
                            [username], one=True)
            assert user, "User not found"
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            assert pw_hash == user[1], "Invalid password"
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        return render_template_string('''<form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
            </form>''')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('index'))

    @app.route('/protected')
    def protected():
        assert g.user, "Login required"
        return f'Secret data for {g.user["username"]}'

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        init_db()
        add_user('test', 'test')
    app.run(debug=True)