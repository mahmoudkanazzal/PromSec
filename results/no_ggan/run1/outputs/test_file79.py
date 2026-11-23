import os
import sys
import logging
import traceback
from pathlib import Path
from flask import Flask, request, session, abort
import MySQLdb
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

def _is_valid_identifier(value: str) -> bool:
    return all(c.isalnum() or c in '-_' for c in value)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    try:
        stock_name = request.form.get('stock_name', '').strip()
        stock_quantity = request.form.get('stock_quantity', '').strip()
        username = session.get('username')
        if not stock_name or not stock_quantity or not username:
            abort(400)
        if not _is_valid_identifier(username) or not _is_valid_identifier(stock_name):
            abort(400)
        try:
            qty = int(stock_quantity)
            if qty <= 0:
                abort(400)
        except ValueError:
            abort(400)
        db_host = os.getenv('DB_HOST')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        if not all([db_host, db_user, db_password, db_name]):
            logger.error('Database configuration missing')
            abort(500)
        conn = None
        try:
            conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name, charset='utf8mb4', use_unicode=True)
            cursor = conn.cursor()
            sql = "INSERT INTO db_table.order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, stock_name, qty))
            conn.commit()
        except MySQLdb.Error:
            if conn:
                conn.rollback()
            logger.exception('Database error')
            abort(500)
        finally:
            if conn:
                conn.close()
        script_path = Path(sys.argv[0]).resolve().parent.parent.joinpath('algorithm.py').resolve()
        if not script_path.is_file():
            logger.error('algorithm.py not found')
            abort(500)
        try:
            result = subprocess.run([sys.executable, str(script_path), 'buy', username, stock_name, str(qty)], capture_output=True, text=True, timeout=30, check=True)
            output = result.stdout.strip()
            return output
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
            logger.exception('Subprocess execution failed')
            abort(500)
    except Exception:
        logger.exception('Unexpected error in buy_order')
        abort(500)

if __name__ == '__main__':
    app.run()