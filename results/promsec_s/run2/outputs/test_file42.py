import os
from flask import Flask, request, Response
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        passwd=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', ''),
        charset='utf8mb4',
        use_unicode=True
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return Response('Registration Failed', mimetype='text/plain')
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return Response('Username already exists', mimetype='text/plain')
                pwd_hash = generate_password_hash(password)
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return Response('You have successfully registered', mimetype='text/plain')
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return Response('Registration Failed', mimetype='text/plain')
    finally:
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return Response('Checkout Failed', mimetype='text/plain')
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE username=%s', (username,))
                user = cur.fetchone()
                if not user:
                    return Response('User not found', mimetype='text/plain')
                user_id = user[0]
                cur.execute('INSERT INTO checkouts (user_id, book_id, checkout_date) VALUES (%s, %s, NOW())', (user_id, book_id))
        conn.commit()
        return Response('Book successfully checked out', mimetype='text/plain')
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return Response('Checkout Failed', mimetype='text/plain')
    finally:
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return Response('Return Failed', mimetype='text/plain')
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE username=%s', (username,))
                user = cur.fetchone()
                if not user:
                    return Response('Checkout record not found', mimetype='text/plain')
                user_id = user[0]
                cur.execute('SELECT id FROM checkouts WHERE user_id=%s AND book_id=%s', (user_id, book_id))
                checkout = cur.fetchone()
                if not checkout:
                    return Response('Checkout record not found', mimetype='text/plain')
                checkout_id = checkout[0]
                cur.execute('DELETE FROM checkouts WHERE id=%s', (checkout_id,))
        conn.commit()
        return Response('Book successfully returned', mimetype='text/plain')
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return Response('Return Failed', mimetype='text/plain')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)