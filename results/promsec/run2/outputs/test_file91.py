import os
import logging
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


def get_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4'
    )


@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Books WHERE Title = %s", (title,))
        if cursor.fetchone():
            return redirect('./add_book')
        cursor.execute(
            "INSERT INTO Books (Title, Author) VALUES (%s, %s)",
            (title, author)
        )
        conn.commit()
        return redirect('./view_books')
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM Members WHERE Username = %s AND Password = %s",
            (username, password)
        )
        if cursor.fetchone():
            return "Login successful"
        return "Invalid credentials"
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title')
    new_author = request.form.get('new_author')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Books SET Author = %s WHERE Title = %s",
            (new_author, title)
        )
        conn.commit()
        return "Author updated successfully"
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title')
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Books WHERE Title = %s", (title,))
        conn.commit()
        return "Book deleted successfully"
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
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
            "SELECT * FROM Books WHERE Title LIKE %s OR Author LIKE %s",
            (pattern, pattern)
        )
        rows = cursor.fetchall()
        return str(rows)
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
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
        cursor.execute("SELECT * FROM Books")
        rows = cursor.fetchall()
        return str(rows)
    except MySQLdb.Error as e:
        app.logger.error("Database error: %s", e)
        return "Internal server error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=False)