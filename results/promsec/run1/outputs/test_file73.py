import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset=os.getenv('DB_CHARSET')
    )

@app.route('/register', methods=['POST'])
def register():
    conn = None
    cur = None
    try:
        username = request.form['username']
        password = request.form['password']
        salt = os.urandom(16)
        pwd_hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
        stored = (pwd_hash + salt).hex()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, stored))
        conn.commit()
        return redirect('/home')
    except Exception:
        return redirect('/home')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    conn = None
    cur = None
    try:
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
        if not row:
            return 'Invalid credentials'
        stored_hex = row[0]
        stored_bytes = bytes.fromhex(stored_hex)
        salt = stored_bytes[32:]
        stored_hash = stored_bytes[:32]
        pwd_hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
        if pwd_hash == stored_hash:
            return redirect('/dashboard')
        else:
            return 'Invalid credentials'
    except Exception:
        return 'Login failed'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    conn = None
    cur = None
    try:
        book_id = request.form['book_id']
        title = request.form['title']
        author = request.form['author']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)', (book_id, title, author))
        conn.commit()
        return 'Book successfully added'
    except Exception:
        return 'Failed to add book'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout():
    conn = None
    cur = None
    try:
        username = request.form['username']
        book_id = request.form['book_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cur.fetchone():
            return 'User not found'
        cur.execute('INSERT INTO checkouts (username, book_id) VALUES (%s, %s)', (username, book_id))
        conn.commit()
        return 'Book successfully checked out'
    except Exception:
        return 'Checkout failed'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book():
    conn = None
    cur = None
    try:
        username = request.form['username']
        book_id = request.form['book_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        if not cur.fetchone():
            return 'Checkout record not found'
        cur.execute('DELETE FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        conn.commit()
        return 'Book successfully returned'
    except Exception:
        return 'Return failed'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT book_id, title, author FROM books')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result)
    except Exception:
        return 'Failed to retrieve books'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)