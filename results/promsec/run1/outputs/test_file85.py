from flask import Flask, request, redirect, session
import os, sys, MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        return "failure"
    username = session.get('username')
    if not username:
        return ("unauthenticated", 401)
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except:
        return "failure"
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'test')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name, charset='utf8mb4')
        cur = conn.cursor()
        sql = "INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cur.execute(sql, (username, stock_name, qty))
        conn.commit()
        return "successful"
    except MySQLdb.Error:
        return "failure"
    finally:
        try:
            if cur:
                cur.close()
        except:
            pass
        try:
            if conn:
                conn.close()
        except:
            pass

if __name__ == '__main__':
    app.run()