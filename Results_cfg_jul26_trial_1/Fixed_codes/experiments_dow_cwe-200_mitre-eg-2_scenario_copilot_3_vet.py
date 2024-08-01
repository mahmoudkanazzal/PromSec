import os
from flask import Flask, request, redirect

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

@app.route('/login', methods=['POST'])
def login():
    try:
        # MySQL database connection code here
        # Check user credentials and login
        # Redirect to '/session' if login is successful
        return redirect('/session')
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run()