#copilot mean_prob: 0.48596494414554725
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

#register url
@app.route('/register', methods=['POST'])
def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   salt = os.urandom(16)
#-copilot next line-#copilot mean_prob: 0.48596494414554725

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   salt = os.urandom(16)
   pwHash = hashlib.sha256(password + salt).hexdigest()
   db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                         user="w sens",         # your username
                         passwd="sens",  # your password
                         db="sens")        # name of the data base

   # The cursor object will let you execute the sql commands
   cur = db.cursor()

   userExists = 0
   sql = "SELECT * FROM User WHERE username = %s"
   cur.execute(sql, [username])
   for row in cur.fetchall():
      if(username == row[1]):
         userExists = 1
   if(not userExists):
      sql = '''INSERT INTO User(username, pw_hash, salt) VALUES(%s, %s, %s)'''
      cur.execute(sql,[username, pwHash, salt])
      db.commit()
      return redirect('/login')
   else:
      db.rollback()

