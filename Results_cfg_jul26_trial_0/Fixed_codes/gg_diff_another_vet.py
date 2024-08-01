import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    cursor = db.cursor()
    cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (data['title'], data['author']))
    db.commit()
    return jsonify({'message': 'Book added successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (data['username'], data['password']))
    user = cursor.fetchone()
    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/update_book_author', methods=['PUT'])
def update_book_author():
    data = request.get_json()
    cursor = db.cursor()
    cursor.execute("UPDATE books SET author = %s WHERE title = %s", (data['author'], data['title']))
    db.commit()
    return jsonify({'message': 'Book author updated successfully'})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    data = request.get_json()
    cursor = db.cursor()
    cursor.execute("DELETE FROM books WHERE title = %s", (data['title'],))
    db.commit()
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", ('%' + keyword + '%', '%' + keyword + '%'))
    books = cursor.fetchall()
    return jsonify({'books': books})

@app.route('/view_all_books', methods=['GET'])
def view_all_books():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run()