import os
import shlex
import getpass
import datetime
from flask import Flask, request, session, make_response
import mysql.connector

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not username:
        return 'unauthenticated', 401
    try:
        qty = int(stock_quantity)
    except (TypeError, ValueError):
        return 'invalid quantity', 400
    conn = None
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT stock_quantity FROM user_portfolio WHERE username = %s', (username,))
        row = cur.fetchone()
        if row:
            new_qty = row[0] + qty
            cur.execute('UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s', (new_qty, username))
            conn.commit()
            return 'updated'
        else:
            cur.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, qty))
            conn.commit()
            return 'initialized'
    except Exception:
        return 'error', 500
    finally:
        if conn:
            conn.close()

@app.route('/run_command', methods=['POST'])
def run_command():
    try:
        command = request.form.get('command')
        if command is None:
            return 'no command', 400
        parts = shlex.split(command)
        if not parts:
            return 'empty command', 400
        whitelist = {'ls', 'whoami', 'date'}
        cmd = parts[0]
        if cmd not in whitelist:
            return 'forbidden', 403
        if len(parts) > 1:
            return 'arguments not allowed', 400
        if cmd == 'ls':
            try:
                entries = os.listdir('.')
                return '\n'.join(entries)
            except OSError as e:
                return str(e), 500
        if cmd == 'whoami':
            return getpass.getuser()
        if cmd == 'date':
            return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return 'unsupported command', 400
    except Exception:
        return 'error', 500

if __name__ == '__main__':
    app.run(debug=False)