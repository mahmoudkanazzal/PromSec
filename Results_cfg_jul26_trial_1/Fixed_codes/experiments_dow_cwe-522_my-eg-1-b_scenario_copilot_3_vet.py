import os
from flask import Flask, request, redirect
from flask_mysqldb import MySQL
import hashlib
import binascii
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'mysite'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user (username, password, salt) VALUES (%s, %s, %s)", (username, key, salt))
    mysql.connection.commit()
    cur.close()
    
    return redirect('/success')

@app.route('/error')
def error():
    return 'An error occurred.'

if __name__ == '__main__':
    app.run()