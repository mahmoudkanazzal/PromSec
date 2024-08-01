import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH")

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    
    cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    
    conn.close()
    
    return jsonify({"message": "Book added successfully"})

@app.route('/search_book', methods=['GET'])
def search_book():
    conn = create_connection()
    cursor = conn.cursor()
    
    title = request.args.get('title')
    
    cursor.execute("SELECT * FROM books WHERE title = ?", (title,))
    books = cursor.fetchall()
    
    conn.close()
    
    return jsonify({"books": books})

@app.route('/update_book', methods=['PUT'])
def update_book():
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    
    cursor.execute("UPDATE books SET author = ? WHERE title = ?", (author, title))
    conn.commit()
    
    conn.close()
    
    return jsonify({"message": "Book updated successfully"})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    conn = create_connection()
    cursor = conn.cursor()
    
    title = request.args.get('title')
    
    cursor.execute("DELETE FROM books WHERE title = ?", (title,))
    conn.commit()
    
    conn.close()
    
    return jsonify({"message": "Book deleted successfully"})

if __name__ == '__main__':
    app.run()
