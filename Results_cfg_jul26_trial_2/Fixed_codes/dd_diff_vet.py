import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
MYSQL_DB = 'library_db'

db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        return jsonify({'message': 'Username already exists'}), 400

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    cursor.execute("INSERT INTO checkouts (username, book_id) VALUES (%s, %s)", (username, book_id))
    db.commit()

    return jsonify({'message': 'Book checked out successfully'})

@app.route('/return', methods=['POST'])
def return_book():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    cursor.execute("DELETE FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({'message': 'Checkout record not found'}), 404

    return jsonify({'message': 'Book returned successfully'})

if __name__ == '__main__':
    app.run(debug=False)