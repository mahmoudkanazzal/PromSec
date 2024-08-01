from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import bcrypt
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password'].encode('utf-8')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    
    if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/update_profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    username = data['username']
    new_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, username))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('query')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT username FROM users WHERE username LIKE %s", ('%' + query + '%',))
    users = cur.fetchall()
    cur.close()
    
    return jsonify({'users': [user['username'] for user in users]})

@app.route('/delete_account', methods=['DELETE'])
def delete_account():
    data = request.get_json()
    username = data['username']
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Account deleted successfully'})

if __name__ == '__main__':
    app.run()