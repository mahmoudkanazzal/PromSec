import os
from flask import Flask, request, redirect
import mysql.connector
import hashlib

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_database = os.environ.get('DB_DATABASE')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_database
)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    cursor = db.cursor()
    username = request.form['username']
    password = hash_password(request.form['password'])
    email = request.form['email']
    
    query = "INSERT INTO User (username, password, email) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, password, email))
    db.commit()
    
    return redirect('/')

if __name__ == '__main__':
    app.run()