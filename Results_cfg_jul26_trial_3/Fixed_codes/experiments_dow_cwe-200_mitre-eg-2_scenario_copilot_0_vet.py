import os
from flask import Flask, request, redirect

app = Flask(__name__)

# Database connection details
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

# Dummy user data for demonstration
users = {
    'user1': {
        'username': 'user1',
        'password': 'hashed_password_1'
    }
}

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            return redirect('/success')
        else:
            return redirect('/cant_login')
    except Exception as e:
        print(e)
        return redirect('/internal_server_error')

if __name__ == '__main__':
    app.run()