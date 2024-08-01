from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    return sqlite3.connect('library.db')

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.json['title']
    author = request.json['author']
    year = request.json['year']

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"INSERT INTO books (title, author, year) VALUES ('{title}', '{author}', {year})"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Book added successfully"}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"SELECT * FROM books WHERE title LIKE '%{keyword}%' OR author LIKE '%{keyword}%'"
    cursor.execute(query)
    
    books = cursor.fetchall()
    conn.close()

    return jsonify(books), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    new_title = request.json.get('title')
    new_author = request.json.get('author')
    new_year = request.json.get('year')

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"UPDATE books SET title='{new_title}', author='{new_author}', year={new_year} WHERE id={book_id}"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Book updated successfully"}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"DELETE FROM books WHERE id={book_id}"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Book deleted successfully"}), 200

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year = request.args.get('year', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"SELECT * FROM books WHERE year={year}"
    cursor.execute(query)
    
    books = cursor.fetchall()
    conn.close()

    return jsonify(books), 200

if __name__ == '__main__':
    app.run(debug=False)
