import os
import logging
from flask import Flask, request, redirect, jsonify
import MySQLdb
import MySQLdb.cursors

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def get_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    if not title or not author:
        return redirect('./add_book')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Books WHERE Title = %s", (title,))
        if cursor.fetchone():
            return redirect('./add_book')
        cursor.execute("INSERT INTO Books (Title, Author) VALUES (%s, %s)", (title, author))
        conn.commit()
        return redirect('./view_books')
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return "An error occurred", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Members WHERE Username = %s AND Password = %s", (username, password))
        if cursor.fetchone():
            return "Login successful"
        else:
            return "Invalid credentials"
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return "An error occurred", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title')
    new_author = request.form.get('new_author')
    if not title or not new_author:
        return "Invalid input", 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Books SET Author = %s WHERE Title = %s", (new_author, title))
        conn.commit()
        return "Author updated successfully"
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return "An error occurred", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title')
    if not title:
        return "Invalid input", 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Books WHERE Title = %s", (title,))
        conn.commit()
        return "Book deleted successfully"
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return "An error occurred", 500
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Title, Author FROM Books WHERE Title LIKE %s OR Author LIKE %s",
            (pattern, pattern)
        )
        rows = cursor.fetchall()
        return jsonify(rows)
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return jsonify([]), 500
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Title, Author FROM Books")
        rows = cursor.fetchall()
        return jsonify(rows)
    except MySQLdb.Error as e:
        logging.error("Database error: %s", e)
        return jsonify([]), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)