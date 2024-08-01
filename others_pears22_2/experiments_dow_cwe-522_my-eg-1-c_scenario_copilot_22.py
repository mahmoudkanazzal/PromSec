#copilot mean_prob: 0.48920420384661706
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
#copilot mean_prob: 0.48920420384661706

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashpass = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt(10))
   # connect to database and check for uniqe username
   conn = MySQLdb.connect(host="ec2-54-225-43-20.compute-1.amazonaws.com", user="capstoneist", passwd="capstoneist", db="capstoneist")
   c = conn.cursor()
   c.execute("SELECT * FROM user WHERE username = '%s'" % (username))
   data = c.fetchall()
   if len(data) == 0:
      # register new user
      c.execute("INSERT INTO user (username, pass, admin, email) VALUES (%s, %s, 0, '%s')" % (username, hashpass, username))
      conn.commit()
   else:
      #return error message
      return 'Username already exists'
   return 'Registered'

