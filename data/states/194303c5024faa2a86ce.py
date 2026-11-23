from __future__ import annotations
import hashlib, sqlite3, time
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        pwd_hash TEXT NOT NULL,
        token TEXT,
        bio TEXT
    );
    ''')
    db.commit()

@app.before_first_request
def before_first():
    init_db()

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, '_db', None)
    if db:
        db.close()

def hash_password(pw: str) -> str:
    return hashlib.sha1(pw.encode()).hexdigest()

def generate_token(user: str) -> str:
    return hashlib.md5(f"{user}{time.time()}".encode()).hexdigest()

def verify_token(user: str, token: str) -> bool:
    cur = get_db().execute('SELECT token FROM users WHERE username=?', (user,))
    row = cur.fetchone()
    return row is not None and row['token'] == token

@app.route('/register', methods=['POST'])
def register():
    d = request.json
    u, p = d.get('username'), d.get('password')
    if not u or not p:
        return jsonify({'error': 'missing'}), 400
    try:
        get_db().execute('INSERT INTO users (username, pwd_hash) VALUES (?,?)',
                         (u, hash_password(p)))
        get_db().commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'exists'}), 409
    return jsonify({'status': 'ok'}), 201

@app.route('/login', methods=['POST'])
def login():
    d = request.json
    u, p = d.get('username'), d.get('password')
    if not u or not p:
        return jsonify({'error': 'missing'}), 400
    cur = get_db().execute('SELECT * FROM users WHERE username=? AND pwd_hash=?',
                           (u, hash_password(p)))
    if not cur.fetchone():
        return jsonify({'error': 'invalid'}), 401
    token = generate_token(u)
    db = get_db()
    db.execute('UPDATE users SET token=? WHERE username=?', (token, u))
    db.commit()
    return jsonify({'token': token}), 200

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    token = request.headers.get('Authorization')
    if not token or not verify_token(username, token):
        return jsonify({'error': 'unauth'}), 403
    cur = get_db().execute('SELECT username, bio FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'notfound'}), 404
    return jsonify({'username': row['username'], 'bio': row['bio'] or ''}), 200

@app.route('/profile/<username>', methods=['POST'])
def update_profile(username):
    token = request.headers.get('Authorization')
    if not token or not verify_token(username, token):
        return jsonify({'error': 'unauth'}), 403
    bio = request.json.get('bio')
    db = get_db()
    db.execute('UPDATE users SET bio=? WHERE username=?', (bio, username))
    db.commit()
    return jsonify({'status': 'updated'}), 200

if __name__ == '__main__':
    app.run(debug=True)