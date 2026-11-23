from __future__ import annotations
import sqlite3, os
from flask import Flask, request, session, redirect, url_for, render_template_string, g

app = Flask(__name__)
# Use environment variable for secret key, fall back to a random key if not set
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

DB_PATH = 'app.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DB_PATH):
        db = sqlite3.connect(DB_PATH)
        db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
        db.commit()
        db.close()

def find_user(username, password):
    db = get_db()
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    cur = db.execute(query, (username, password))
    return cur.fetchone()

def add_user(username, password):
    db = get_db()
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    db.commit()

@app.route('/')
def index():
    if 'user_id' in session:
        db = get_db()
        user = db.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        return render_template_string('<h1>Hello {{user.username}}</h1><a href="{{url_for(\'logout\')}}">Logout</a>', user=user)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user(username, password)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return render_template_string('<p>Invalid credentials</p><a href="{{url_for(\'login\')}}">Try again</a>')
    return render_template_string('''
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
        <a href="{{url_for('register')}}">Register</a>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            add_user(username, password)
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template_string('<p>User exists</p><a href="{{url_for(\'register\')}}">Try again</a>')
    return render_template_string('''
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Register">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

app.teardown_appcontext(close_db)

if __name__ == '__main__':
    init_db()
    app.run(debug=False)