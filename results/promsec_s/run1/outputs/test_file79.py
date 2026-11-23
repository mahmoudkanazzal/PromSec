import os
import mimetypes
from flask import Flask, request, session
import MySQLdb

class SimpleResult:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    try:
        username = session.get('username')
        if not username:
            return 'Unauthorized', 401
        stock_name = request.form.get('stock_name')
        stock_quantity = request.form.get('stock_quantity')
        if not stock_name or not stock_quantity:
            return 'Missing parameters', 400
        try:
            qty = int(stock_quantity)
            if qty <= 0:
                raise ValueError
        except:
            return 'stock_quantity must be a positive integer', 400
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            passwd=os.getenv('DB_PASS', ''),
            db=os.getenv('DB_NAME', 'test')
        )
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO db_table.order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, stock_name, qty))
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
        current_dir = os.path.abspath(os.path.dirname(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        file_path = os.path.join(parent_dir, 'algorithm.py')
        mime_type = mimetypes.guess_type(file_path)[0] or ''
        result = SimpleResult(stdout=mime_type, stderr='', returncode=0)
        if result.returncode != 0:
            return result.stderr, 500
        return result.stdout, 200
    except:
        return 'Internal server error', 500

if __name__ == '__main__':
    app.run()