from __future__ import print_function
import os, sqlite3, hashlib, subprocess
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
# Use environment variable for secret key, fallback to a random key
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False

@app.route('/')
def index():
    if 'user' in session:
        return render_template_string('''
        <h1>Hello {{user}}</h1>
        <form action="{{url_for('run_command')}}" method="post">
        Command: <input name="cmd"><input type="submit" value="Run">
        </form>
        <a href="{{url_for('logout')}}">Logout</a>
        ''', user=session['user'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials', 401
    return render_template_string('''
    <form method="post">
    Username: <input name="username"><br>
    Password: <input name="password" type="password"><br>
    <input type="submit" value="Login">
    </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/run', methods=['POST'])
def run_command():
    if 'user' not in session:
        return redirect(url_for('login'))
    cmd = request.form.get('cmd', '')
    # Execute without invoking a shell to prevent injection
    subprocess.run(['echo', cmd], capture_output=True, text=True)
    return 'Command executed'

if __name__ == '__main__':
    init_db()
    create_user('admin', 'admin')
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)