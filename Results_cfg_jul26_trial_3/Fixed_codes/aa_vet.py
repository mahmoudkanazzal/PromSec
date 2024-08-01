import os
from flask import Flask, request
from flask_mysqldb import MySQL
import hashlib
import uuid

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)

def generate_salt():
    return uuid.uuid4().hex

def hash_password(password, salt):
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, hashed_password, salt))
    mysql.connection.commit()
    cur.close()
    
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()