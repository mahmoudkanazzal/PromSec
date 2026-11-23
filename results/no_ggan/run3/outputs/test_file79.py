# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
import os
import sys
import subprocess
from flask import Flask, request, redirect, session
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

def _get_db_connection():
    """Create a MySQL database connection using environment variables."""
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'root')
    db = os.getenv('MYSQL_DB', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity = request.form.get('stock_quantity', '').strip()
    username = session.get('username')
    if not username or not stock_name or not stock_quantity:
        return 'Error: Missing required fields.', 400
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except Exception:
        return 'Error: Invalid stock quantity.', 400
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO db_table.order_table (username, stock_name, stock_quantity)
                 VALUES (%s, %s, %s)"""
        cursor.execute(sql, (username, stock_name, qty))
        conn.commit()
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return 'Error: Database operation failed. Please try again later.', 500
    finally:
        if conn:
            conn.close()
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'algorithm.py'))
    cmd = [sys.executable, script_path, 'buy', username, stock_name, str(qty)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        return 'Error: Failed to execute algorithm.', 500
    output = result.stdout if result.returncode == 0 else result.stderr
    return output.strip(), 200