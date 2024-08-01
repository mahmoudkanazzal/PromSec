import os
import hashlib
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

def hash_password(password, salt):
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    salt = os.urandom(32).hex()
    hashed_password = hash_password(password, salt)
    
    cnx = mysql.connector.connect(user='user', password=os.environ.get('DB_PASSWORD'),
                                  host='localhost', database='mydatabase')
    cursor = cnx.cursor()
    
    query = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, hashed_password, salt))
    
    cnx.commit()
    cursor.close()
    cnx.close()
    
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()