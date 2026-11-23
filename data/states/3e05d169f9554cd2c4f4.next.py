from __future__ import annotations

import os
from flask import Flask, request, redirect, url_for, session, render_template_string

# Retrieve password from environment variable; default to empty string if not set
PASSWORD = os.getenv('APP_PASSWORD', '')

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    @app.route('/')
    def index():
        if session.get('logged_in'):
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if check_credentials(username, password):
                login_user(username)
                return redirect(url_for('dashboard'))
            else:
                return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
        return render_template_string(LOGIN_TEMPLATE)

    @app.route('/dashboard')
    def dashboard():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        user = session.get('user')
        return f"<h1>Welcome, {user}!</h1><p><a href='{url_for('logout')}'>Logout</a></p>"

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))

    return app

def check_credentials(username: str, password: str) -> bool:
    return password == PASSWORD

def login_user(username: str) -> None:
    session['logged_in'] = True
    session['user'] = username

def logout_user() -> None:
    session.clear()

LOGIN_TEMPLATE = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
<form method=post>
  <input type=text name=username placeholder="Username"><br>
  <input type=password name=password placeholder="Password"><br>
  <input type=submit value=Login>
</form>
"""

if __name__ == '__main__':
    app = create_app()
    # Run with debugging disabled and bind to localhost only
    app.run(debug=False, host='127.0.0.1', port=5000)