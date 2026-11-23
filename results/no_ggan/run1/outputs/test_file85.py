import os
import logging
from typing import Optional
import MySQLdb
from flask import Flask, request, session, jsonify, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_secret_key = os.getenv('FLASK_SECRET_KEY')
if not _secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable must be set and non‑empty')
app.secret_key = _secret_key
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_COOKIE_SECURE') == '1'

def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f'Environment variable {var_name} is required and must be non‑empty')
    return value

def get_db_connection() -> MySQLdb.connections.Connection:
    host = _require_env('DB_HOST')
    user = _require_env('DB_USER')
    password = _require_env('DB_PASSWORD')
    db = _require_env('DB_NAME')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

def _get_user_id() -> Optional[int]:
    username = session.get('username')
    if username is None:
        return None
    try:
        return int(username)
    except (ValueError, TypeError):
        return None

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form
    stock_name = data.get('stock_name')
    stock_quantity = data.get('stock_quantity')
    user_id = _get_user_id()
    if user_id is None:
        abort(401, description='Authentication required.')
    if not stock_name or stock_quantity is None:
        return jsonify({'status': 'failure', 'error': 'Missing required parameters.'}), 400
    if len(stock_name) > 100:
        return jsonify({'status': 'failure', 'error': 'Stock name too long.'}), 400
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'status': 'failure', 'error': 'Invalid stock quantity.'}), 400
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)',
                (user_id, stock_name, qty)
            )
        conn.commit()
        conn.close()
        return jsonify({'status': 'successful'}), 200
    except MySQLdb.Error:
        logger.exception('Database error during buy_order')
        return jsonify({'status': 'failure', 'error': 'Internal server error.'}), 500

if __name__ == '__main__':
    app.run()