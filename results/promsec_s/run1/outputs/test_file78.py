from flask import Flask, request, redirect, session
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity_raw = request.form.get('stock_quantity', '').strip()
    username = session.get('username')
    if not stock_name:
        return 'stock_name is required', 400
    if not stock_quantity_raw.isdigit():
        return 'stock_quantity must be a positive integer', 400
    stock_quantity = int(stock_quantity_raw)
    if stock_quantity <= 0:
        return 'stock_quantity must be a positive integer', 400
    if not username:
        return 'User not logged in', 400
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            passwd=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DB')
        )
        cursor = conn.cursor()
        sql = "INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)"
        cursor.execute(sql, (stock_name, stock_quantity, username))
        conn.commit()
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
    return redirect('/')

if __name__ == '__main__':
    app.run()