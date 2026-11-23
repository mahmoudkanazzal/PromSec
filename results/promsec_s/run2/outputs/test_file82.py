import os
import shlex
import mimetypes
from flask import Flask, request, session, abort, Response
import mysql.connector

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASS', ''),
        database=os.getenv('DB_NAME', '')
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
        if quantity <= 0:
            abort(400)
    except Exception:
        abort(400)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        select_sql = "SELECT stock_quantity FROM portfolio WHERE username=%s AND stock_name=%s"
        cursor.execute(select_sql, (username, stock_name))
        row = cursor.fetchone()
        if row:
            update_sql = "UPDATE portfolio SET stock_quantity = stock_quantity + %s WHERE username=%s AND stock_name=%s"
            cursor.execute(update_sql, (quantity, username, stock_name))
            conn.commit()
            return Response("updated", mimetype='text/plain')
        else:
            insert_sql = "INSERT INTO portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
            cursor.execute(insert_sql, (username, stock_name, quantity))
            conn.commit()
            return Response("initialized", mimetype='text/plain')
    except mysql.connector.Error:
        abort(500)
    finally:
        if conn:
            conn.close()

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form.get('command')
    if not command:
        abort(400)
    whitelist = {"ls", "whoami", "date"}
    try:
        parts = shlex.split(command)
        if not parts or parts[0] not in whitelist:
            abort(400)
        mime_type, _ = mimetypes.guess_type(parts[0])
        if mime_type:
            return Response(mime_type, mimetype='text/plain')
        else:
            return Response("unknown command", mimetype='text/plain')
    except Exception:
        abort(500)

if __name__ == '__main__':
    app.run(debug=False)