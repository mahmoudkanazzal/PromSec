import os
from flask import Flask, request, session
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        return 'unauthenticated', 401
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)",
            (username, stock_name, stock_quantity)
        )
        conn.commit()
        return 'successful'
    except MySQLdb.Error:
        return 'failure'
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run()