import os
import shlex
import subprocess
import MySQLdb
from flask import Flask, request, session, abort, Response

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24).hex()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')

ALLOWED_COMMANDS = {'ls', 'date', 'whoami'}

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        abort(400)
    try:
        quantity = int(stock_quantity)
    except (ValueError, TypeError):
        abort(400)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stock_quantity FROM user_portfolio WHERE username=%s', (username,))
        row = cursor.fetchone()
        if row:
            new_quantity = row[0] + quantity
            cursor.execute('UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s', (new_quantity, username))
            conn.commit()
            return 'updated'
        else:
            cursor.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, quantity))
            conn.commit()
            return 'initialized'
    finally:
        if conn:
            conn.close()

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form.get('command', '').strip()
    if not command:
        abort(400)
    try:
        args = shlex.split(command)
    except ValueError:
        abort(400)
    if not args or args[0] not in ALLOWED_COMMANDS:
        abort(403)
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return Response(result.stdout, mimetype='text/plain')
    except subprocess.CalledProcessError as e:
        err = e.stderr if e.stderr else 'Command execution failed.'
        return Response(err, status=500, mimetype='text/plain')
    except Exception:
        return Response('Internal server error.', status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=False)