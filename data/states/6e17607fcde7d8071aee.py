from __future__ import annotations
import os, sqlite3, hashlib
from flask import Flask, request, session, redirect, url_for, g, render_template_string

app = Flask(__name__)
app.secret_key = 'devkey'
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

app.teardown_appcontext(close_db)

def init_db():
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
    db.commit()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def query_user(username: str):
    cur = get_db().execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()

def register_user(username: str, password: str) -> bool:
    if query_user(username): return False
    pw_hash = hash_pw(password)
    db = get_db()
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, pw_hash))
    db.commit()
    return True

def verify_password(stored: str, pw: str) -> bool:
    return stored == hash_pw(pw)

@app.before_request
def load_user():
    g.user = None
    uid = session.get('user_id')
    if uid:
        cur = get_db().execute('SELECT * FROM users WHERE id = ?', (uid,))
        g.user = cur.fetchone()

@app.route('/')
def index():
    if g.user:
        return f'Logged in as {g.user["username"]} <a href="/logout">Logout</a>'
    return 'Not logged in <a href="/login">Login</a> <a href="/register">Register</a>'

login_form = '''<form method="post">
Username: <input name="username"><br>
Password: <input type="password" name="password"><br>
<input type="submit" value="Login">
</form>'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = query_user(request.form['username'])
        if user and verify_password(user['password'], request.form['password']):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        return 'Invalid credentials', 401
    return render_template_string(login_form)

register_form = '''<form method="post">
Username: <input name="username"><br>
Password: <input type="password" name="password"><br>
<input type="submit" value="Register">
</form>'''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if register_user(request.form['username'], request.form['password']):
            return redirect(url_for('login'))
        return 'User exists', 409
    return render_template_string(register_form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)