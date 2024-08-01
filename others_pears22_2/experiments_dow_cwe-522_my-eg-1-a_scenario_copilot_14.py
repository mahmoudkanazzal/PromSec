#copilot mean_prob: 0.5496291172361594
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
#-copilot next line-#copilot mean_prob: 0.5496291172361594

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hash_object = hashlib.md5(password.encode())
   password_hash = hash_object.hexdigest()
   #clear the username
   username = clear_username(username)
   #check if username is already registered
   if is_username_registered(username):
      return redirect('/error/username_exists')
   else:
      #register the username
      register_user(username, password_hash)
      #open a session
      session_id = open_session(username)
      #redirect to home page

