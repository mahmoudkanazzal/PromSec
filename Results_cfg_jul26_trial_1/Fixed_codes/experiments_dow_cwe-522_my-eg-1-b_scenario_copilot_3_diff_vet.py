import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import MySQLdb

app = Flask(__name__)
bcrypt = Bcrypt()

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()
    
    return jsonify(message='User registered successfully')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user[2], password):
        return jsonify(message='Login successful')
    else:
        return jsonify(message='Invalid username or password')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    
    cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
    db.commit()
    
    return jsonify(message='Book added successfully')

@app.route('/checkout_book', methods=['POST'])
def checkout_book():
    data = request.get_json()
    book_id = data.get('book_id')
    username = data.get('username')
    
    cursor.execute("UPDATE books SET checked_out_by = %s WHERE id = %s", (username, book_id))
    db.commit()
    
    return jsonify(message='Book checked out successfully')

@app.route('/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    book_id = data.get('book_id')
    
    cursor.execute("UPDATE books SET checked_out_by = NULL WHERE id = %s", (book_id,))
    db.commit()
    
    return jsonify(message='Book returned successfully')

@app.route('/view_books', methods=['GET'])
def view_books():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    
    return jsonify(books)

if __name__ == '__main__':
    app.run()