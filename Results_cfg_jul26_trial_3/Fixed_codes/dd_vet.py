from flask import Flask, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database='cwe_900')
        cursor = cnx.cursor()

        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        cnx.commit()

        cursor.close()
        cnx.close()

        return jsonify({'message': 'User registered successfully'})
    except mysql.connector.Error as err:
        return jsonify({'error': 'Failed to register user'})

if __name__ == '__main__':
    app.run()