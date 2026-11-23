import os
from flask import Flask, request, jsonify
import MySQLdb
from MySQLdb.cursors import DictCursor

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True
    )

def validate_field(value):
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None

@app.route('/add_book', methods=['POST'])
def add_book():
    title = validate_field(request.form.get('title'))
    author = validate_field(request.form.get('author'))
    if not title or not author:
        return jsonify({'error': 'Missing title or author'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM Books WHERE Title = %s', (title,))
        if cursor.fetchone():
            return jsonify({'error': 'Book already exists'}), 409
        cursor.execute('INSERT INTO Books (Title, Author) VALUES (%s, %s)', (title, author))
        conn.commit()
        return jsonify({'message': 'Book added'}), 201
    except Exception:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    username = validate_field(request.form.get('username'))
    password = validate_field(request.form.get('password'))
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM Members WHERE username = %s AND password = %s', (username, password))
        if cursor.fetchone():
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = validate_field(request.form.get('title'))
    author = validate_field(request.form.get('author'))
    if not title or not author:
        return jsonify({'error': 'Missing title or author'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Books SET Author = %s WHERE Title = %s', (author, title))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({'error': 'Book not found'}), 404
        conn.commit()
        return jsonify({'message': 'Author updated'}), 200
    except Exception:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = validate_field(request.form.get('title'))
    if not title:
        return jsonify({'error': 'Missing title'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Books WHERE Title = %s', (title,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({'error': 'Book not found'}), 404
        conn.commit()
        return jsonify({'message': 'Book deleted'}), 200
    except Exception:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/search_books', methods=['GET'])
def search_books():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute('SELECT Title, Author FROM Books WHERE Title LIKE %s OR Author LIKE %s', (pattern, pattern))
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
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
        cursor = conn.cursor(DictCursor)
        cursor.execute('SELECT Title, Author FROM Books')
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)