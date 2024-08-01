import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = os.getenv('DATABASE')

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL, copies INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO books (title, author, copies) VALUES (?, ?, ?)", (title, author, 0))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Book added successfully'})

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    conn.close()
    
    if book:
        return jsonify({'id': book[0], 'title': book[1], 'author': book[2], 'copies': book[3]})
    else:
        return jsonify({'message': 'Book not found'})

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json()
    book_id = data.get('id')
    copies = data.get('copies')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE books SET copies = copies + ? WHERE id=?", (copies, book_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Copies updated successfully'})

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM books ORDER BY title")
    catalog = [{'id': row[0], 'title': row[1], 'author': row[2], 'copies': row[3]} for row in c.fetchall()]
    conn.close()
    
    return jsonify(catalog)

if __name__ == '__main__':
    create_table()
    app.run()
