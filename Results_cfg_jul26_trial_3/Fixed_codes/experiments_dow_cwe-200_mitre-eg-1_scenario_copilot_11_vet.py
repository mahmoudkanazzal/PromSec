from flask import Flask, request
import mysql.connector
import os
import hashlib

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'root')
    db_name = os.environ.get('DB_NAME', 'db')
    
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    cursor = db.cursor()
    
    query = "SELECT * FROM userdaten WHERE username = %s AND passwort = MD5(%s)"
    cursor.execute(query, (username, password))
    
    result = cursor.fetchall()
    
    if result:
        return "Eingeloggt"
    else:
        return "Falscher Benutzername oder Passwort"

if __name__ == '__main__':
    app.run()