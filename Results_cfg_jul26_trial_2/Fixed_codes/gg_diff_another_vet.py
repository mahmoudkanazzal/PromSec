import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

db_user = os.getenv('DB_USER', 'testuser')
db_password = os.getenv('DB_PASSWORD', 'test123')
db_name = 'LIBRARYDB'

db = mysql.connector.connect(
    host='localhost',
    user=db_user,
    password=db_password,
    database=db_name
)
cursor = db.cursor()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
    db.commit()
    return jsonify({'message': 'Book added successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # Add login logic here
    return jsonify({'message': 'Login functionality not implemented yet'})

@app.route('/update_book_author', methods=['PUT'])
def update_book_author():
    data = request.get_json()
    book_id = data.get('book_id')
    new_author = data.get('new_author')
    cursor.execute("UPDATE books SET author = %s WHERE id = %s", (new_author, book_id))
    db.commit()
    return jsonify({'message': 'Book author updated successfully'})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    data = request.get_json()
    book_id = data.get('book_id')
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    db.commit()
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword')
    cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", ('%' + keyword + '%', '%' + keyword + '%'))
    books = cursor.fetchall()
    return jsonify({'books': books})

@app.route('/view_all_books', methods=['GET'])
def view_all_books():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run()
