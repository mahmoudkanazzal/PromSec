import os
import hashlib
from flask import Flask, request, redirect, url_for, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'change_this_secret_key')

def get_db_connection():
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', 'library'),
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor,
        autocommit=False
    )
    return conn

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    pwd_hash = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, pwd_hash))
        conn.commit()
        return redirect(url_for('home'))
    except MySQLdb.IntegrityError as e:
        if e.args[0] == 1062:
            abort(409)
        else:
            app.logger.error(f"IntegrityError in register: {e}")
            abort(500)
    except Exception as e:
        app.logger.error(f"Exception in register: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT password FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row['password'], password):
            return redirect(url_for('dashboard'))
        else:
            abort(401, description='Invalid credentials')
    except Exception as e:
        app.logger.error(f"Exception in login: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    book_id = request.form.get('book_id')
    title = request.form.get('title')
    author = request.form.get('author')
    if not book_id or not title or not author:
        abort(400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)"
        cursor.execute(sql, (book_id, title, author))
        conn.commit()
        return ('Book successfully added', 201)
    except MySQLdb.IntegrityError as e:
        if e.args[0] == 1062:
            abort(409)
        else:
            app.logger.error(f"IntegrityError in add_book: {e}")
            abort(500)
    except Exception as e:
        app.logger.error(f"Exception in add_book: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if not cursor.fetchone():
            abort(404, description='User not found')
        cursor.execute("SELECT 1 FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            abort(404, description='Book not found')
        sql = "INSERT INTO checkouts (username, book_id) VALUES (%s, %s)"
        cursor.execute(sql, (username, book_id))
        conn.commit()
        return ('Book successfully checked out', 200)
    except MySQLdb.IntegrityError as e:
        if e.args[0] == 1062:
            abort(409)
        else:
            app.logger.error(f"IntegrityError in checkout: {e}")
            abort(500)
    except Exception as e:
        app.logger.error(f"Exception in checkout: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_check = "SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s"
        cursor.execute(sql_check, (username, book_id))
        if not cursor.fetchone():
            abort(404, description='Checkout record not found')
        sql_delete = "DELETE FROM checkouts WHERE username = %s AND book_id = %s"
        cursor.execute(sql_delete, (username, book_id))
        conn.commit()
        return ('Book successfully returned', 200)
    except Exception as e:
        app.logger.error(f"Exception in return: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT book_id, title, author FROM books")
        books = cursor.fetchall()
        return jsonify(books), 200
    except Exception as e:
        app.logger.error(f"Exception in view_books: {e}")
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/home', methods=['GET'])
def home():
    return ('Welcome to the library system', 200)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return ('User dashboard', 200)

if __name__ == '__main__':
    app.run(debug=False)