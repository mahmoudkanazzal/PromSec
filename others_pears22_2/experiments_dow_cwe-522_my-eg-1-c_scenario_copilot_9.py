#copilot mean_prob: 0.6585314989430422
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
#copilot mean_prob: 0.6585314989430422

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   #create cursor to work with
   cur = mysql.connection.cursor()
   #execute query to insert the user into the db
   cur.execute("INSERT INTO user(username, password) VALUES(%s, %s)", (username, hashpass))
   #commit to the db
   mysql.connection.commit()
   #close connection
   cur.close()
   #redirect to the login page and pass the username
   return redirect('/login?username=' + username)

