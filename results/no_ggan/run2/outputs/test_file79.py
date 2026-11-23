from flask import Flask, request, session
import os, sys, subprocess, MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity = request.form.get('stock_quantity', '').strip()
    username = session.get('username')
    if not username or not stock_name or not stock_quantity:
        return 'Error: Missing required parameters.', 400
    try:
        stock_quantity_int = int(stock_quantity)
        if stock_quantity_int <= 0:
            raise ValueError
    except ValueError:
        return 'Error: Invalid stock quantity.', 400
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', 'root')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        sql = "INSERT INTO db_table.order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, stock_name, stock_quantity_int))
        conn.commit()
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return 'Error: Database operation failed. Please try again later.', 500
    finally:
        if conn:
            conn.close()
    algorithm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'algorithm.py'))
    cmd = [sys.executable, algorithm_path, 'buy', username, stock_name, str(stock_quantity_int)]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    except Exception:
        return 'Error: Failed to execute algorithm.', 500
    output = result.stdout.strip()
    return output

if __name__ == '__main__':
    app.run()