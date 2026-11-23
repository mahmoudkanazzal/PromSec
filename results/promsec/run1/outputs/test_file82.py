import os
import shlex
from datetime import datetime
import getpass
from flask import Flask, request, session, Response
from mysql.connector import connect as mysql_connect

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24).hex()

_db_host = os.getenv('DB_HOST')
_db_user = os.getenv('DB_USER')
_db_pass = os.getenv('DB_PASS')
_db_name = os.getenv('DB_NAME')
if not all([_db_host, _db_user, _db_pass, _db_name]):
    raise RuntimeError('Database configuration environment variables must be set')
db_config = {
    'host': _db_host,
    'user': _db_user,
    'password': _db_pass,
    'database': _db_name
}

def _is_positive_int(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False

_ALLOWED_COMMANDS = {'date', 'uptime', 'whoami'}

def _execute_allowed_command(cmd):
    if cmd == 'date':
        return datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')
    if cmd == 'uptime':
        try:
            with open('/proc/uptime', 'r') as f:
                parts = f.read().split()
                seconds = float(parts[0])
            days = int(seconds // 86400)
            hrs = int((seconds % 86400) // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{days} days, {hrs:02}:{mins:02}:{secs:02}"
        except Exception:
            return 'uptime information not available'
    if cmd == 'whoami':
        return getpass.getuser()
    raise ValueError('Unsupported command')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = session.get('stock_name')
    stock_quantity = session.get('stock_quantity')
    username = session.get('username')
    if not all([stock_name, stock_quantity, username]):
        return Response('invalid', status=400)
    if not _is_positive_int(stock_quantity):
        return Response('invalid quantity', status=400)
    requested_qty = int(stock_quantity)
    conn = None
    cur = None
    try:
        conn = mysql_connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT stock_quantity FROM user_portfolio WHERE username = %s", (username,))
        row = cur.fetchone()
        if row:
            try:
                existing_qty = int(row[0])
            except (TypeError, ValueError):
                return Response('corrupt data', status=500)
            new_qty = existing_qty + requested_qty
            cur.execute("UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s", (new_qty, username))
            conn.commit()
            body = 'updated'
        else:
            cur.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, requested_qty))
            conn.commit()
            body = 'initialized'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return Response(body, status=200)

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form.get('command')
    if not command:
        return Response('no command', status=400)
    try:
        tokens = shlex.split(command)
    except ValueError:
        return Response('command not allowed', status=403)
    if len(tokens) != 1 or tokens[0] not in _ALLOWED_COMMANDS:
        return Response('command not allowed', status=403)
    try:
        output = _execute_allowed_command(tokens[0])
    except Exception:
        return Response('execution error', status=500)
    return Response(output, status=200)

if __name__ == '__main__':
    app.run(debug=False)