from __future__ import annotations
import hashlib, sqlite3
from flask import Flask, request, g, jsonify, abort
app = Flask(__name__)
DATABASE = 'shop.db'
def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db
@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_db', None)
    if db: db.close()
def init_db():
    db = get_db()
    db.executescript('''
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE,
 password_hash TEXT);
CREATE TABLE IF NOT EXISTS items(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT,
 quantity INTEGER,
 price REAL);
 ''')
    db.commit()
def hash_password(pwd): return hashlib.sha256(pwd.encode()).hexdigest()
def check_password(pwd, h): return hash_password(pwd)==h
def add_user(username, password):
    db=get_db()
    cur=db.cursor()
    cur.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',
                (username,hash_password(password)))
    db.commit()
    return cur.lastrowid
def get_user(username):
    cur=get_db().cursor()
    cur.execute('SELECT * FROM users WHERE username=?',(username,))
    return cur.fetchone()
def add_item(name, qty, price):
    cur=get_db().cursor()
    cur.execute('INSERT INTO items(name,quantity,price) VALUES(?,?,?)',
                (name,qty,price))
    get_db().commit()
    return cur.lastrowid
def list_items():
    cur=get_db().cursor()
    cur.execute('SELECT * FROM items')
    return [dict(r) for r in cur.fetchall()]
def update_stock(item_id, delta):
    cur=get_db().cursor()
    cur.execute('UPDATE items SET quantity=quantity+? WHERE id=?',(delta,item_id))
    get_db().commit()
def require_auth(f):
    def wrapper(*a,**kw):
        auth=request.authorization
        if not auth: abort(401)
        u=get_user(auth.username)
        if not u or not check_password(auth.password,u['password_hash']): abort(403)
        return f(*a,**kw)
    wrapper.__name__=f.__name__
    return wrapper
@app.route('/login',methods=['POST'])
def login():
    d=request.get_json()
    if not d or 'username' not in d or 'password' not in d: return jsonify(error='missing'),400
    u=get_user(d['username'])
    if u and check_password(d['password'],u['password_hash']):
        token=hashlib.sha256((d['username']+d['password']).encode()).hexdigest()
        return jsonify(token=token)
    return jsonify(error='invalid'),403
@app.route('/add_item',methods=['POST'])
@require_auth
def api_add_item():
    d=request.get_json()
    if not d or not all(k in d for k in ('name','quantity','price')):
        return jsonify(error='missing'),400
    iid=add_item(d['name'],int(d['quantity']),float(d['price']))
    return jsonify(id=iid),201
@app.route('/items',methods=['GET'])
@require_auth
def api_items():
    return jsonify(list_items())
@app.route('/update_stock',methods=['POST'])
@require_auth
def api_update_stock():
    d=request.get_json()
    if not d or not all(k in d for k in ('id','delta')):
        return jsonify(error='missing'),400
    update_stock(int(d['id']),int(d['delta']))
    return jsonify(status='ok')
if __name__=='__main__':
    with app.app_context(): init_db()
    app.run()