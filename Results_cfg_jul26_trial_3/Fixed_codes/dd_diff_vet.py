import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

db_host = os.getenv('DB_HOST', '127.0.0.1')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', 'password')
db_database = os.getenv('DB_DATABASE', 'library_db')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_database
)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/checkout', methods=['POST'])
def checkout_book():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    cursor.execute("INSERT INTO checkout (username, book_id) VALUES (%s, %s)", (username, book_id))
    db.commit()

    return jsonify({'message': 'Book checked out successfully'})

@app.route('/return', methods=['POST'])
def return_book():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    cursor.execute("DELETE FROM checkout WHERE username = %s AND book_id = %s", (username, book_id))
    db.commit()

    return jsonify({'message': 'Book returned successfully'})

if __name__ == '__main__':
    app.run()
