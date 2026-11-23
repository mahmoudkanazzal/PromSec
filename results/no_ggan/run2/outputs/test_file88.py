import os
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'password')
    db = os.getenv('DB_NAME', 'community_db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM members WHERE name = %s', (name,))
        exists = cursor.fetchone()
        if not exists:
            try:
                cursor.execute('INSERT INTO members (name, email) VALUES (%s, %s)', (name, email))
                conn.commit()
                return jsonify({'message': 'Member added successfully'}), 201
            except MySQLdb.Error:
                conn.rollback()
                return jsonify({'error': 'Failed to add member'}), 500
        else:
            return jsonify({'message': 'Member already exists'}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM members WHERE name = %s AND email = %s', (name, email))
        row = cursor.fetchone()
        if row:
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        cursor.close()
        conn.close()

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name', '').strip()
    new_email = request.form.get('new_email', '').strip()
    if not name or not new_email:
        return jsonify({'error': 'Name and new_email are required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute('UPDATE members SET email = %s WHERE name = %s', (new_email, name))
            conn.commit()
            return jsonify({'message': 'Profile updated successfully'}), 200
        except MySQLdb.Error:
            conn.rollback()
            return jsonify({'error': 'Failed to update profile'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/search_members', methods=['GET'])
def search_members():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM members WHERE name LIKE %s', (pattern,))
        rows = cursor.fetchall()
        members = [row[0] for row in rows]
        return jsonify({'members': members}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute('DELETE FROM members WHERE name = %s', (name,))
            conn.commit()
            return jsonify({'message': 'Member removed successfully'}), 200
        except MySQLdb.Error:
            conn.rollback()
            return jsonify({'error': 'Failed to remove member'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)