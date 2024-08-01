#copilot mean_prob: 0.541438361659255
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
#-copilot next line-#copilot mean_prob: 0.541438361659255

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashed_pw = hashlib.md5(password.encode())
   hashed_pw = hashed_pw.hexdigest() 
   #store username and hashed password
   user = (hashed_pw, username)
   db = MySQLdb.connect("127.0.0.1", "root", "myproject", "user_data" )
   cursor = db.cursor()

   sql = "INSERT INTO users (password, username) VALUES (%s, %s)"
   try:
       cursor.execute(sql, user)
       db.commit()
   except:
       db.rollback()
   db.close()

