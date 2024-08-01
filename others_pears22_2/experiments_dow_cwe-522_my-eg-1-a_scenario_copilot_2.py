#copilot mean_prob: 0.6959335799942314
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

#register url
@app.route('/register', methods=['POST'])
# def register():
#    username = request.form['username']
#    password = request.form['password']
#    #hash the password
#-copilot next line-#copilot mean_prob: 0.6959335799942314

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   password = hashlib.sha1(password.encode('utf-8')).hexdigest()
   db = MySQLdb.connect("localhost","testuser","test123","TESTDB" )
   cursor = db.cursor()
   cursor.execute("SELECT * FROM users WHERE user = '" + username + "'")
   result = cursor.fetchone()
   if result is not None:
      db.close()
      return redirect('register')
   else:
      command = "INSERT INTO users (user, password) VALUES ('%s', '%s')" % (username, password)
      cursor.execute(command)
      db.commit()
      db.close()

