from __future__ import print_function
import os
import sqlite3
import hashlib
import subprocess
import shlex
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

def verify_password(stored_hash, password):
    return stored_hash == hashlib.sha256(password.encode()).hexdigest()

login_form = '''
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method=post>
  Username: <input type=text name=username><br>
  Password: <input type=password name=password><br>
  <input type=submit value=Login>
</form>
'''

run_form = '''
<!doctype html>
<title>Run Command</title>
<h2>Run a command</h2>
<form method=post>
  Command: <input type=text name=cmd><br>
  <input type=submit value=Run>
</form>
<pre>{{output}}</pre>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form.get('username', '')
        pwd = request.form.get('password', '')
        user = get_user(uname)
        if user and verify_password(user[2], pwd):
            session['user'] = uname
            return redirect(url_for('run_command'))
        else:
            return render_template_string(login_form + '<p>Invalid credentials</p>')
    return render_template_string(login_form)

@app.route('/run', methods=['GET', 'POST'])
def run_command():
    if 'user' not in session:
        return redirect(url_for('login'))
    output = ''
    if request.method == 'POST':
        cmd_str = request.form.get('cmd', '')
        if cmd_str:
            try:
                args = shlex.split(cmd_str)
                result = subprocess.run(args, capture_output=True, text=True)
                output = result.stdout + result.stderr
            except Exception as e:
                output = f'Error: {e}'
    return render_template_string(run_form, output=output)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form.get('username', '')
        pwd = request.form.get('password', '')
        if get_user(uname) is None:
            create_user(uname, pwd)
            return redirect(url_for('login'))
        else:
            return render_template_string('<p>User exists</p>')
    return render_template_string('''
<!doctype html>
<title>Register</title>
<h2>Register</h2>
<form method=post>
  Username: <input type=text name=username><br>
  Password: <input type=password name=password><br>
  <input type=submit value=Register>
</form>
''')

if __name__ == '__main__':
    init_db()
    app.run(debug=False)