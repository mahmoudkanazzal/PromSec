#copilot mean_prob: 0.6888640327628691
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from functools import wraps
from flask import abort
from flask import g, Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def ensure_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if session['username'] is None:
            return redirect('/login')
        return f(*args, **kws)            
    return decorated_function

#the login page
@app.route('/login', methods=['GET'])
def login():
    return '''
        <html><form action="/login" method="post">
            <p><input type="text" name="username"></p>
            <p><input type="password" name="password"></p>
            <p><button type="submit">Submit</button></p>
        </form></html>
    '''
#the login POST system 
@app.route('/login', methods=['POST'])
def do_login():
    if request.form['username'] == 'admin' and request.form['password'] == 'password':
        session['username'] = request.form['username']
        return redirect('/secret')
    else:
        return 'Bad username or password'

#the home page
@app.route('/')
def index():
    return '''<html>
    Hello! <a href='./login'>Login here</a>
    </html>'''

#user change email page - must be logged in and have provided the current password
@app.route('/change_email', methods=['POST'])
@ensure_logged_in
# def change_email():
#     old_email = request.form['old_email']
#     new_email = request.form['new_email']
#     confirm_password = request.form['confirm_password']
#     username = session['username']
#     db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="db")
#-copilot next line-
#copilot mean_prob: 0.6888640327628691

def change_email():
    old_email = request.form['old_email']
    new_email = request.form['new_email']
    confirm_password = request.form['confirm_password']
    username = session['username']
    db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="db")
    cur = db.cursor()
    cur.execute("SELECT password from users where username='" + username + "';")
    data = cur.fetchone()
    password = data[0]
    if old_email == '':
        return "Please enter an old email"
    elif new_email == '':
        return "Please enter a new email"
    elif password == ' ':
        return "Please enter your password"
    elif confirm_password == ' ':
        return "Please enter your password"
    elif old_email != request.form['old_email']:
        return "You did not enter the correct old email"
    elif new_email != request.form['new_email']:
        return "You did not enter the correct new email"
    elif password != request.form['confirm_password']:
        return "Your new password does not match the confirmation password you entered"
    elif new_email.find('@') == -1:
        return "Please enter a valid email address"
    else:
        cur.execute("UPDATE users SET email='" + new_email + "' where username='" + username + "';")
        db.commit()
        return redirect('/secret')

