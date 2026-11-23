from flask import Flask, request, redirect, jsonify
import MySQLdb
import hashlib
import os

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', 'cisco123'),
        db=os.getenv('DB_NAME', 'library_db')
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    salt = os.urandom(16)
    pwd_hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
    stored = (pwd_hash + salt).hex()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, stored))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/home')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            stored_hex = row[0]
            stored_bytes = bytes.fromhex(stored_hex)
            salt = stored_bytes[-16:]
            stored_hash = stored_bytes[:32]
            pwd_hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
            if pwd_hash == stored_hash:
                return redirect('/dashboard')
        return "Invalid credentials"
    except Exception as e:
        print(e)
        return "Invalid credentials"
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
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)", (book_id, title, author))
        conn.commit()
        return "Book successfully added"
    except Exception as e:
        print(e)
        return "Failed to add book"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.execute("INSERT INTO checkouts (username, book_id) VALUES (%s, %s)", (username, book_id))
            conn.commit()
            return "Book successfully checked out"
        else:
            return "User not found"
    except Exception as e:
        print(e)
        return "Book successfully checked out"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
        if cursor.fetchone():
            cursor.execute("DELETE FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
            conn.commit()
            return "Book successfully returned"
        else:
            return "Checkout record not found"
    except Exception as e:
        print(e)
        return "Checkout record not found"
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
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result)
    except Exception as e:
        print(e)
        return "Failed to retrieve books"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)