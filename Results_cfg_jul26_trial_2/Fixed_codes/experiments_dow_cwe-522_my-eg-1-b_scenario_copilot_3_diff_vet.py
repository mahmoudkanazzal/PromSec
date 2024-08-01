import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'library'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    
    if user and bcrypt.check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data['title']
    author = data['author']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Book added successfully'})

@app.route('/checkout_book', methods=['POST'])
def checkout_book():
    data = request.get_json()
    book_id = data['book_id']
    user_id = data['user_id']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO checkout (book_id, user_id) VALUES (%s, %s)", (book_id, user_id))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Book checked out successfully'})

@app.route('/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    book_id = data['book_id']
    user_id = data['user_id']
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM checkout WHERE book_id = %s AND user_id = %s", (book_id, user_id))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Book returned successfully'})

@app.route('/view_books', methods=['GET'])
def view_books():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    cur.close()
    
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run(debug=True)
