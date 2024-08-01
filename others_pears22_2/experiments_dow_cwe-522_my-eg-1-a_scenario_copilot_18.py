#copilot mean_prob: 0.47053552270662813
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
#-copilot next line-#copilot mean_prob: 0.47053552270662813

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashed = hash_password(password)
   db = connectToDB()
   c = db.cursor()
   #see if they are already in the DB
   c.execute("SELECT * FROM users WHERE username = '%s'" % (username))
   res = c.fetchall()
   if len(res) != 0:
      return 'username already taken'
   else:
      c.execute("INSERT INTO users VALUES ('%s', '%s')" % (username , hashed))
      db.commit()
      db.close()
      return '%s has been registered' % (username)

