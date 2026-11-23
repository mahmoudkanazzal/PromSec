import os
import MySQLdb
import MySQLdb.cursors
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'library')


def get_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True,
        cursorclass=MySQLdb.cursors.DictCursor
    )


def validate_fields(required):
    missing = [field for field in required if field not in request.form]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    return None


@app.route('/register', methods=['POST'])
def register():
    error_response = validate_fields(['username', 'password'])
    if error_response:
        return error_response

    username = request.form['username']
    password = request.form['password']
    hashed = generate_password_hash(password)

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
            (username, hashed)
        )
        conn.commit()
        return jsonify({'message': 'User registered'}), 201
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/checkout', methods=['POST'])
def checkout():
    error_response = validate_fields(['username', 'book_id'])
    if error_response:
        return error_response

    username = request.form['username']
    book_id = request.form['book_id']

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_id = user['id']
        cursor.execute(
            'INSERT INTO checkouts (user_id, book_id, checkout_date) VALUES (%s, %s, NOW())',
            (user_id, book_id)
        )
        conn.commit()
        return jsonify({'message': 'Book checked out'}), 200
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/return', methods=['POST'])
def return_book():
    error_response = validate_fields(['username', 'book_id'])
    if error_response:
        return error_response

    username = request.form['username']
    book_id = request.form['book_id']

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_id = user['id']
        cursor.execute(
            'SELECT id FROM checkouts WHERE user_id = %s AND book_id = %s',
            (user_id, book_id)
        )
        checkout = cursor.fetchone()
        if not checkout:
            return jsonify({'error': 'Checkout record not found'}), 404
        cursor.execute(
            'DELETE FROM checkouts WHERE id = %s',
            (checkout['id'],)
        )
        conn.commit()
        return jsonify({'message': 'Book returned'}), 200
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # In production, use a WSGI server.