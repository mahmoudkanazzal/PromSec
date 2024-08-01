import os
from flask import Flask, request, jsonify
import mysql.connector
import hashlib
import uuid

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

cursor = db.cursor()

def hash_password(password, salt):
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    salt = uuid.uuid4().hex
    hashed_password = hash_password(password, salt)

    try:
        cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, hashed_password, salt))
        db.commit()
        return jsonify({'message': 'User registered successfully'})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})

if __name__ == '__main__':
    app.run()