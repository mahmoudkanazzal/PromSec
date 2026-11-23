from __future__ import annotations
import os, sys, yaml, sqlite3, hashlib, pickle, requests
from flask import Flask, request, jsonify

def load_config(path):
    if not os.path.isfile(path):
        sys.exit(f"Config file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT)""")
    conn.commit()
    return conn

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def add_user(conn, username, password):
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username,password_hash) VALUES (?,?)",
                (username, hash_password(password)))
    conn.commit()
    return cur.lastrowid

def get_user(conn, uid):
    cur = conn.cursor()
    cur.execute("SELECT id,username FROM users WHERE id=?", (uid,))
    row = cur.fetchone()
    return {"id": row[0], "username": row[1]} if row else None

def cache_load(p):
    if os.path.isfile(p):
        with open(p, 'rb') as f:
            return pickle.load(f)
    return {}

def cache_save(p, data):
    with open(p, 'wb') as f:
        pickle.dump(data, f)

def create_app(cfg, db):
    app = Flask(__name__)

    @app.route('/health')
    def health():
        return jsonify(status='ok')

    @app.route('/user', methods=['POST'])
    def create_user():
        d = request.get_json() or {}
        u = d.get('username')
        pw = d.get('password')
        if not u or not pw:
            return jsonify(error='Missing fields'), 400
        try:
            uid = add_user(db, u, pw)
        except sqlite3.IntegrityError:
            return jsonify(error='User exists'), 409
        return jsonify(id=uid, username=u), 201

    @app.route('/user/<int:uid>')
    def fetch_user(uid):
        u = get_user(db, uid)
        if not u:
            return jsonify(error='Not found'), 404
        return jsonify(u)

    @app.route('/external')
    def external():
        url = cfg.get('external_url')
        if not url:
            return jsonify(error='No external URL configured'), 500
        r = requests.get(url, timeout=5)
        return jsonify(data=r.json())

    return app

def main():
    cfg_path = os.getenv('CONFIG_PATH', 'config.yaml')
    cfg = load_config(cfg_path)
    db = init_db(cfg.get('db_path', 'app.db'))
    cache = cache_load(cfg.get('cache_file', 'cache.pkl'))
    app = create_app(cfg, db)
    app.run(host='0.0.0.0', port=int(cfg.get('port', 5000)))

if __name__ == '__main__':
    main()