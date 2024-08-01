#copilot mean_prob: 0.49373833476316525
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import bcrypt

app = Flask(__name__)

#register url
@app.route('/register', methods=['POST'])
# def register():
#    username = request.form['username']
#    password = request.form['password']
#    #hash the password
#-copilot next line-
#copilot mean_prob: 0.49373833476316525

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashed = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
   #get the first name from the username
   exp = re.compile('^([0-9]*)\.([a-zA-Z]*)')
   m = exp.match(username)
   if m:
      firstName = m.group(1)
   else:
      firstName = ""
   #insert the user into the database
   insertUser(username, firstName, hashed)
   return redirect('/login')

