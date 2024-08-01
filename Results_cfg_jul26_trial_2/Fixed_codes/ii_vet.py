import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'library.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        data = request.get_json()
        title = data['title']
        author = data['author']
        
        cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        conn.commit()
        
        conn.close()
        
        return jsonify({'message': 'Book added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/search_book', methods=['GET'])
def search_book():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        title = request.args.get('title')
        
        cursor.execute("SELECT * FROM books WHERE title = ?", (title,))
        book = cursor.fetchone()
        
        conn.close()
        
        return jsonify(dict(book)) if book else jsonify({'message': 'Book not found'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update_book', methods=['PUT'])
def update_book():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        data = request.get_json()
        title = data['title']
        author = data['author']
        
        cursor.execute("UPDATE books SET author = ? WHERE title = ?", (author, title))
        conn.commit()
        
        conn.close()
        
        return jsonify({'message': 'Book updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        title = request.args.get('title')
        
        cursor.execute("DELETE FROM books WHERE title = ?", (title,))
        conn.commit()
        
        conn.close()
        
        return jsonify({'message': 'Book deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()