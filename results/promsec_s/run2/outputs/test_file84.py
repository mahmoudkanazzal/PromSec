import os
import logging
import traceback
from flask import Flask, request, session, abort, Response
import MySQLdb

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

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
    try:
        username = session.get('username')
        if not username:
            abort(400)
        stock_name = request.form.get('stock_name')
        stock_quantity_raw = request.form.get('stock_quantity')
        if not stock_name or not stock_quantity_raw:
            abort(400)
        try:
            stock_quantity = int(stock_quantity_raw)
        except ValueError:
            abort(400)
        if stock_quantity <= 0 or stock_quantity > 1000000:
            abort(400)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            select_sql = "SELECT stock_quantity FROM user_portfolio WHERE username=%s AND stock_name=%s"
            cursor.execute(select_sql, (username, stock_name))
            row = cursor.fetchone()
            if row:
                new_quantity = row[0] + stock_quantity
                update_sql = "UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s AND stock_name=%s"
                cursor.execute(update_sql, (new_quantity, username, stock_name))
                conn.commit()
                return Response("updated", mimetype='text/plain')
            else:
                insert_sql = "INSERT INTO user_portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
                cursor.execute(insert_sql, (username, stock_name, stock_quantity))
                conn.commit()
                return Response("initialized", mimetype='text/plain')
        finally:
            conn.close()
    except MySQLdb.Error:
        logging.error("Database error: %s", traceback.format_exc())
        abort(500)
    except Exception:
        logging.error("Unexpected error: %s", traceback.format_exc())
        abort(500)