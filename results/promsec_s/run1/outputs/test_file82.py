import os
import logging
import shlex
import MySQLdb
from flask import Flask, request, session, abort, g
import getpass
from datetime import datetime

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_name = os.getenv('DB_NAME')
if not all([db_host, db_user, db_pass, db_name]):
    raise RuntimeError('Missing required database environment variables')

def get_db():
    if not hasattr(g, 'db'):
        g.db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4', use_unicode=True)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        abort(401)
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        abort(400)
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except ValueError:
        abort(400)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT quantity FROM portfolio WHERE username=%s AND stock_name=%s', (username, stock_name))
        row = cur.fetchone()
        if row:
            cur.execute('UPDATE portfolio SET quantity=quantity+%s WHERE username=%s AND stock_name=%s', (qty, username, stock_name))
            conn.commit()
            return 'updated'
        else:
            cur.execute('INSERT INTO portfolio (username, stock_name, quantity) VALUES (%s, %s, %s)', (username, stock_name, qty))
            conn.commit()
            return 'initialized'
    except Exception:
        conn.rollback()
        logging.exception('Error processing buy_order')
        abort(500)

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form.get('command')
    if not command:
        abort(400)
    try:
        parts = shlex.split(command)
        if not parts:
            abort(400)
        cmd = parts[0]
        if cmd not in {'ls', 'whoami', 'date'}:
            abort(403)
        if cmd == 'ls':
            return '\n'.join(os.listdir('.'))
        if cmd == 'whoami':
            return getpass.getuser()
        if cmd == 'date':
            return datetime.now().isoformat()
    except Exception:
        logging.exception('Error processing run_command')
        abort(500)

if __name__ == '__main__':
    app.run(debug=False)