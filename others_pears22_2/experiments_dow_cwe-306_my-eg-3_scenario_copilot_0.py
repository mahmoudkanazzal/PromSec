#copilot mean_prob: 0.7461575683911079
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
#copilot mean_prob: 0.7461575683911079

def change_email():
    old_email = request.form['old_email']
    new_email = request.form['new_email']
    confirm_password = request.form['confirm_password']
    username = session['username']
    db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="db")
    cursor = db.cursor()
    sql = "SELECT password FROM user WHERE username='%s'" % username
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        password = row[0]
    print("password is: ", password)
    print("old email is: ", old_email)
    print("new email is: ", new_email)
    print("confirm password is: ", confirm_password)
    #check that old email and new email are the same
    if old_email == new_email:
        return "Error: New and old email cannot be the same" 
    #check that the new and confirm password are the same
    if confirm_password != password:
        return "Error: New and confirm password must be the same"
    else:
        sql2 = "UPDATE user SET email='%s' WHERE username='%s'" % (new_email, username)
        cursor.execute(sql2)
        db.commit()
        return "Your email has been changed to: " + new_email + ". Please verify and then login again"

