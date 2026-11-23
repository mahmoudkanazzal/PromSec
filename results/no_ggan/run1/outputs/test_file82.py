import os
import shlex
import subprocess
from flask import Flask, request, abort, jsonify, session
import MySQLdb

required_vars = ['FLASK_SECRET_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')


def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True
    )


@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    stock_name = request.form.get('stock_name')
    stock_quantity_raw = request.form.get('stock_quantity')
    if not username or not stock_name or stock_quantity_raw is None:
        abort(400)
    try:
        stock_quantity = int(stock_quantity_raw)
        if stock_quantity < 0:
            raise ValueError
    except ValueError:
        abort(400)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stock_quantity FROM user_portfolio WHERE username=%s AND stock_name=%s",
            (username, stock_name)
        )
        row = cursor.fetchone()
        if row:
            new_quantity = row[0] + stock_quantity
            cursor.execute(
                "UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s AND stock_name=%s",
                (new_quantity, username, stock_name)
            )
            conn.commit()
            return jsonify({"status": "updated", "stock_quantity": new_quantity})
        else:
            cursor.execute(
                "INSERT INTO user_portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)",
                (username, stock_name, stock_quantity)
            )
            conn.commit()
            return jsonify({"status": "initialized", "stock_quantity": stock_quantity})
    finally:
        if conn:
            conn.close()


@app.route('/run_command', methods=['POST'])
def run_command():
    command_str = request.form.get('command')
    if not command_str:
        abort(400)
    try:
        args = shlex.split(command_str)
    except ValueError:
        abort(400)
    if not args:
        abort(400)
    whitelist = {'date', 'uptime', 'whoami'}
    if args[0] not in whitelist:
        abort(403)
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({"output": result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr.strip()}), 400


if __name__ == '__main__':
    app.run(debug=False)