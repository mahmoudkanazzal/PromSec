from __future__ import annotations
import os, sqlite3, hashlib, tempfile
from flask import Flask, request, session, redirect, url_for, g, render_template_string

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24).hex()
DATABASE = 'users.db'
TMP_DIR = tempfile.gettempdir()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    db.commit()

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def get_user(username):
    cur = get_db().execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()

def add_user(username, password):
    db = get_db()
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
    db.commit()

def login_user(user):
    session['user_id'] = user['id']
    session['username'] = user['username']

def logout_user(): session.clear()

def write_temp_file(username):
    path = os.path.join(TMP_DIR, f'temp_{username}.txt')
    with open(path, 'w') as f:
        f.write(f'User {username} accessed')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*a, **kw):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*a, **kw)
    return decorated

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if get_user(u) is None: add_user(u, p); return redirect(url_for('login'))
        return 'User exists', 400
    return render_template_string('<form method="post">Username: <input name="username"><br>Password: <input name="password" type="password"><br><input type="submit" value="Register"></form>')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        user = get_user(u)
        if user and user['password'] == hash_password(p):
            login_user(user); write_temp_file(u); return redirect(url_for('protected'))
        return 'Invalid credentials', 401
    return render_template_string('<form method="post">Username: <input name="username"><br>Password: <input name="password" type="password"><br><input type="submit" value="Login"></form>')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return f'Hello, {session.get("username")}!'

if __name__ == '__main__':
    init_db()
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    app.run(host=host, port=5000)