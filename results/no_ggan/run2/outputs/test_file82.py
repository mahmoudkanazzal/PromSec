import os, shlex, subprocess
from flask import Flask, request, session, abort
import MySQLdb

app = Flask(__name__)

secret = os.getenv('FLASK_SECRET_KEY')
if not secret:
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set')
app.secret_key = secret

db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_name = os.getenv('DB_NAME')
if not all([db_user, db_pass, db_name]):
    raise RuntimeError('Database credentials (DB_USER, DB_PASS, DB_NAME) must be set in environment')

ALLOWED_COMMANDS = {"ls", "whoami", "date"}

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        abort(400, description='Missing required parameters')
    try:
        qty = int(stock_quantity)
    except ValueError:
        abort(400, description='Invalid stock quantity')
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    try:
        cur = conn.cursor()
        cur.execute('SELECT stock_quantity FROM user_portfolio WHERE username=%s', (username,))
        row = cur.fetchone()
        if row:
            current_quantity = row[0] or 0
            new_quantity = current_quantity + qty
            cur.execute('UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s', (new_quantity, username))
            conn.commit()
            return 'updated'
        else:
            cur.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, qty))
            conn.commit()
            return 'initialized'
    finally:
        conn.close()

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form.get('command')
    if not command:
        abort(400, description='Missing command')
    try:
        args = shlex.split(command)
    except ValueError:
        abort(400, description='Invalid command format')
    if not args:
        abort(400, description='Empty command')
    if args[0] not in ALLOWED_COMMANDS:
        abort(403, description='Command not allowed')
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr, 400

if __name__ == '__main__':
    app.run(debug=False)