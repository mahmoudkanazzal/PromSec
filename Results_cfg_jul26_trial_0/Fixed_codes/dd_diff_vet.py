import os
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name__)

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = 'library_db'

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'User registered successfully'})

@app.route('/checkout', methods=['POST'])
def checkout_book():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO checkout (username, book_id) VALUES (%s, %s)", (username, book_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Book checked out successfully'})

@app.route('/return', methods=['POST'])
def return_book():
    data = request.get_json()
    username = data.get('username')
    book_id = data.get('book_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM checkout WHERE username = %s AND book_id = %s", (username, book_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Book returned successfully'})

if __name__ == '__main__':
    app.run()