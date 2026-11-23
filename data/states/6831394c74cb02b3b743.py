from flask import Flask, request, session, g, redirect, url_for, render_template_string
import sqlite3, hashlib, yaml, subprocess

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'users.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL)''')
    db.commit()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user(username):
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()

def create_user(username, password):
    db = get_db()
    pw_hash = hash_password(password)
    db.execute('INSERT INTO users (username, password_hash) VALUES (?,?)',
               (username, pw_hash))
    db.commit()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def login_user(username):
    session['user'] = username

def logout_user():
    session.pop('user', None)

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def parse_yaml(yaml_str):
    return yaml.load(yaml_str)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if get_user(uname) is None:
            create_user(uname, pwd)
            login_user(uname)
            return redirect(url_for('profile'))
    return render_template_string('''
        <h2>Register</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Register">
        </form>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = get_user(uname)
        if user and verify_password(user['password_hash'], pwd):
            login_user(uname)
            return redirect(url_for('profile'))
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template_string('''
        <h2>Welcome {{user}}</h2>
        <a href="{{url_for('yaml_endpoint')}}">Submit YAML</a><br>
        <a href="{{url_for('logout')}}">Logout</a>
    ''', user=session['user'])

@app.route('/yaml', methods=['GET', 'POST'])
@login_required
def yaml_endpoint():
    result = ''
    if request.method == 'POST':
        data = request.form['yaml']
        try:
            obj = parse_yaml(data)
            result = str(obj)
        except Exception as e:
            result = 'Error: ' + str(e)
    return render_template_string('''
        <h2>YAML Parser</h2>
        <form method="post">
            <textarea name="yaml" rows="10" cols="40"></textarea><br>
            <input type="submit" value="Parse">
        </form>
        <pre>{{result}}</pre>
        <a href="{{url_for('profile')}}">Back</a>
    ''', result=result)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)