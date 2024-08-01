import os
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO members (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Member added successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM members WHERE email = %s AND password = %s", (email, password))
    member = cur.fetchone()
    cur.close()
    
    if member:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/update_profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    name = data['name']
    email = data['email']
    new_email = data['new_email']
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE members SET name = %s, email = %s WHERE email = %s", (name, new_email, email))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/search_members', methods=['GET'])
def search_members():
    search_term = request.args.get('search_term')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM members WHERE name LIKE %s OR email LIKE %s", ('%' + search_term + '%', '%' + search_term + '%'))
    members = cur.fetchall()
    cur.close()
    
    return jsonify({'members': members})

@app.route('/remove_member', methods=['DELETE'])
def remove_member():
    data = request.get_json()
    email = data['email']
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM members WHERE email = %s", (email,))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Member removed successfully'})

if __name__ == '__main__':
    app.run()