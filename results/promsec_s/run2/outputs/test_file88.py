import os
from flask import Flask, request, jsonify
import MySQLdb
from MySQLdb import Error

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', ''),
        charset='utf8mb4',
        autocommit=False
    )

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return jsonify({'message': 'Missing name or email'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM members WHERE name = %s', (name,))
                if cur.fetchone():
                    return jsonify({'message': 'Member already exists'}), 200
                cur.execute('INSERT INTO members (name, email) VALUES (%s, %s)', (name, email))
                conn.commit()
                return jsonify({'message': 'Member added successfully'}), 200
    except Error:
        return jsonify({'message': 'Failed to add member'}), 500

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return jsonify({'message': 'Missing name or email'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM members WHERE name = %s AND email = %s', (name, email))
                if cur.fetchone():
                    return jsonify({'message': 'Login successful'}), 200
                else:
                    return jsonify({'message': 'Invalid credentials'}), 401
    except Error:
        return jsonify({'message': 'Server error'}), 500

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name', '').strip()
    new_email = request.form.get('new_email', '').strip()
    if not name or not new_email:
        return jsonify({'message': 'Missing name or new_email'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE members SET email = %s WHERE name = %s', (new_email, name))
                if cur.rowcount == 0:
                    conn.rollback()
                    return jsonify({'message': 'Member not found'}), 404
                conn.commit()
                return jsonify({'message': 'Profile updated successfully'}), 200
    except Error:
        return jsonify({'message': 'Failed to update profile'}), 500

@app.route('/search_members', methods=['GET'])
def search_members():
    term = request.args.get('term', '').strip()
    like_term = f"%{term}%"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM members WHERE name LIKE %s', (like_term,))
                rows = cur.fetchall()
                members = [row[0] for row in rows]
                return jsonify({'members': members}), 200
    except Error:
        return jsonify({'message': 'Search failed'}), 500

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'message': 'Missing name'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM members WHERE name = %s', (name,))
                if cur.rowcount == 0:
                    conn.rollback()
                    return jsonify({'message': 'Member not found'}), 404
                conn.commit()
                return jsonify({'message': 'Member removed successfully'}), 200
    except Error:
        return jsonify({'message': 'Failed to remove member'}), 500

if __name__ == '__main__':
    app.run(debug=False)