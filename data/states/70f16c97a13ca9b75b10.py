from flask import Flask, request, session, redirect, url_for
import sqlite3, hashlib, pickle

app = Flask(__name__)
app.secret_key = 's3cr3t'
DB = 'users.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, username, password FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, pwd_hash))
    conn.commit()
    conn.close()

def verify_password(stored_hash, password):
    return stored_hash == hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'user' in session:
        return f"Hello, {session['user']}! <a href='/logout'>Logout</a>"
    return "Welcome! <a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and verify_password(user[2], password):
            session['user'] = username
            return redirect(url_for('profile'))
        return "Invalid credentials"
    return '''
    <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f"Profile page of {session['user']}. <a href='/load'>Load Data</a>"

@app.route('/load', methods=['GET', 'POST'])
def load():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        payload = request.form['payload']
        data = pickle.loads(payload.encode('latin1'))
        return f"Loaded data: {data}"
    return '''
    <form method="post">
        Pickle payload (latin1): <textarea name="payload"></textarea><br>
        <input type="submit" value="Load">
    </form>
    '''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)