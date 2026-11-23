from flask import Flask, request, redirect, session
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change_me')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        return ('Bad Request', 400)
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except ValueError:
        return ('Bad Request', 400)
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)",
        (stock_name, qty, username)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()