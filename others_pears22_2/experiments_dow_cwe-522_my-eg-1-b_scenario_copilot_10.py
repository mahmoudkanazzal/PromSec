#copilot mean_prob: 0.6023667988223983
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
#-copilot next line-#copilot mean_prob: 0.6023667988223983

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   salt = os.urandom(16)
   encryptedPW = hashlib.sha256(password.encode('UTF-8')+salt).hexdigest()
   email = request.form['email']
   phone = request.form['phone']
   #query to insert a user
   query = "INSERT into users (username, password, salt, email, phone) values (%s, %s, %s, %s, %s)"
   data = (username, encryptedPW, salt, email, phone)
   try:
      cur.execute(query, data)
      db.commit()
      return redirect('/login')
   except (MySQLdb.Error, MySQLdb.Warning) as e:
      db.rollback()    
      return redirect('/register')

