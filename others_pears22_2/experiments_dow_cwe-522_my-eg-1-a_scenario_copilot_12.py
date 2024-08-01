#copilot mean_prob: 0.5512395744884128
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
#-copilot next line-#copilot mean_prob: 0.5512395744884128

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hash_input = username + password
   hashed_password = hashlib.sha256(hash_input.encode()).hexdigest()
   db = MySQLdb.connect(host="localhost", user="root", passwd="password",db="re_reg")
   cursor = db.cursor()
   sql = "SELECT * from users where username = '" + username + "'"
   #check if username exists
   if cursor.execute(sql) == 1:
      #its exists, so return error
      error = "Username already exists"
      db.close()
      return error
   else:
      #insert username and hashed password into db
      sql = "INSERT INTO users (username, password, matches) VALUES ('" + username + "','" + hashed_password + "',0);"
      cursor = db.cursor()
      cursor.execute(sql)
      db.commit()
      db.close()
      #proceed to main
   return redirect("/")

