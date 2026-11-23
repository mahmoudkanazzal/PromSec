from __future__ import annotations
import sqlite3, hashlib, requests, os, getpass
from flask import Flask, request, session, redirect, url_for, render_template_string, g

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())

DATABASE = 'users.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

def init_db():
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)')
    db.commit()

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_user(username, password):
    db = get_db()
    try:
        db.execute('INSERT INTO users (username,password_hash) VALUES (?,?)',
                   (username, hash_pw(password)))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def find_user(username):
    cur = get_db().execute('SELECT id,username,password_hash FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    return {'id':row[0],'username':row[1],'password_hash':row[2]} if row else None

def login_user(user):
    session['uid'] = user['id']

def current_user():
    uid = session.get('uid')
    if not uid:
        return None
    cur = get_db().execute('SELECT id,username,password_hash FROM users WHERE id=?', (uid,))
    row = cur.fetchone()
    return {'id':row[0],'username':row[1],'password_hash':row[2]} if row else None

def external_api():
    r = requests.get('https://httpbin.org/get', timeout=5)
    return r.json()

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        if create_user(request.form['username'], request.form['password']):
            return redirect(url_for('login'))
        return 'User exists',400
    return render_template_string('''<form method="post">
Username:<input name="username"><br>
Password:<input name="password" type="password"><br>
<input type="submit" value="Register">
</form>''')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = find_user(request.form['username'])
        if u and u['password_hash']==hash_pw(request.form['password']):
            login_user(u)
            return redirect(url_for('protected'))
        return 'Invalid',401
    return render_template_string('''<form method="post">
Username:<input name="username"><br>
Password:<input name="password" type="password"><br>
<input type="submit" value="Login">
</form>''')

@app.route('/protected')
def protected():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    api = external_api()
    who = getpass.getuser()
    return f'Hello {u["username"]}! API says {api["url"]}. Server user {who}'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=='__main__':
    with app.app_context():
        init_db()
    app.run(host='127.0.0.1',port=5000)