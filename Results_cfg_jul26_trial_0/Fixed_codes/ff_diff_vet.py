import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_json()
    name = data['name']
    email = data['email']
    
    query = "INSERT INTO members (name, email) VALUES (%s, %s)"
    cursor.execute(query, (name, email))
    db.commit()
    
    return jsonify({'message': 'Member added successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    name = data['name']
    email = data['email']
    
    query = "SELECT * FROM members WHERE name = %s AND email = %s"
    cursor.execute(query, (name, email))
    result = cursor.fetchone()
    
    if result:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/update_email', methods=['PUT'])
def update_email():
    data = request.get_json()
    name = data['name']
    new_email = data['new_email']
    
    query = "UPDATE members SET email = %s WHERE name = %s"
    cursor.execute(query, (new_email, name))
    db.commit()
    
    return jsonify({'message': 'Email updated successfully'})

@app.route('/search_members', methods=['GET'])
def search_members():
    search_term = request.args.get('search_term')
    
    query = "SELECT * FROM members WHERE name LIKE %s OR email LIKE %s"
    cursor.execute(query, ('%' + search_term + '%', '%' + search_term + '%'))
    results = cursor.fetchall()
    
    return jsonify({'members': results})

@app.route('/remove_member', methods=['DELETE'])
def remove_member():
    data = request.get_json()
    name = data['name']
    
    query = "DELETE FROM members WHERE name = %s"
    cursor.execute(query, (name,))
    db.commit()
    
    return jsonify({'message': 'Member removed successfully'})

if __name__ == '__main__':
    app.run()