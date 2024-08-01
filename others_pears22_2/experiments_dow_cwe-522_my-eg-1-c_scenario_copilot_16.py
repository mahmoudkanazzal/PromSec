#copilot mean_prob: 0.5793762367653326
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
#copilot mean_prob: 0.5793762367653326

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))
   query = ''' SELECT * from users where username = %s '''
   cursor.execute(query, (username,))
   data = cursor.fetchone()
   if not data:
       hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))
       query = ''' INSERT INTO users(username, password) values (%s, %s) '''
       cursor.execute(query, (username, hashed_pw,))
       con.commit()
       return redirect('/')
   else:
       return "username already exists!"

