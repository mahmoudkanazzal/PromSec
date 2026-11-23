import os
from flask import Flask, request, redirect, url_for
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASS', 'test123')
    db = os.getenv('DB_NAME', 'LIBRARYDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM Books WHERE Title = %s', (title,))
        if cursor.fetchone():
            return redirect(url_for('add_book'))
        cursor.execute('INSERT INTO Books (Title, Author) VALUES (%s, %s)', (title, author))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('view_books'))

@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT Password FROM Members WHERE Username = %s', (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if row and check_password_hash(row[0], password):
        return 'Login successful'
    return 'Invalid credentials'

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title')
    new_author = request.form.get('new_author')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE Books SET Author = %s WHERE Title = %s', (new_author, title))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Author updated successfully'

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Books WHERE Title = %s', (title,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Book deleted successfully'

@app.route('/search_books', methods=['GET'])
def search_books():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Books WHERE Title LIKE %s OR Author LIKE %s', (pattern, pattern))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return str(rows)

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Books')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return str(rows)

if __name__ == '__main__':
    app.run(debug=False)