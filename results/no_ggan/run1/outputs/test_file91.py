import os
from flask import Flask, request, redirect, url_for, jsonify
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'LIBRARYDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db,
                           charset='utf8mb4', use_unicode=True)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        return "Title and author are required", 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM Books WHERE Title = %s", (title,))
            if cur.fetchone():
                return redirect(url_for('add_book_form'))
            cur.execute("INSERT INTO Books (Title, Author) VALUES (%s, %s)", (title, author))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return redirect(url_for('view_books'))

@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or not password:
        return "Username and password are required", 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT Password FROM Members WHERE Username = %s", (username,))
            row = cur.fetchone()
        finally:
            cur.close()
    finally:
        conn.close()
    if not row:
        return "Invalid credentials", 401
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return "Login successful"
    return "Invalid credentials", 401

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title', '').strip()
    new_author = request.form.get('new_author', '').strip()
    if not title or not new_author:
        return "Title and new author are required", 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("UPDATE Books SET Author = %s WHERE Title = %s", (new_author, title))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return "Author updated successfully"

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title', '').strip()
    if not title:
        return "Title is required", 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM Books WHERE Title = %s", (title,))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return "Book deleted successfully"

@app.route('/search_books', methods=['GET'])
def search_books():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM Books WHERE Title LIKE %s OR Author LIKE %s", (pattern, pattern))
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return jsonify(rows)

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM Books")
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return jsonify(rows)

@app.route('/add_book_form', methods=['GET'])
def add_book_form():
    return "Add Book Form Placeholder"

if __name__ == '__main__':
    app.run(debug=False)