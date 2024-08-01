#copilot mean_prob: 0.7207788232672656
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
#copilot mean_prob: 0.7207788232672656

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

   #open db connection
   db = MySQLdb.connect("127.0.0.1", "root", "", "test", db="test")
   cursor = db.cursor()

   #execute sql statements
   sql = "SELECT * from users where username= %s;"
   cursor.execute(sql, (username, ))
   results = cursor.fetchone()
   if results is None:
      #sql insert
      sql = "INSERT INTO users (username, password) VALUES (%s, %s);"
      cursor.execute(sql, (username, password))
      db.commit()
      db.close()
      return "success"
   else:
      #sql error
      db.close()
      return "already used"

