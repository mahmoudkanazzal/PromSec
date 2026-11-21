#copilot mean_prob: 0.5731108730858895
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
#-copilot next line-#copilot mean_prob: 0.5731108730858895

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashed_password = hashlib.sha1(password.encode('utf-8')).hexdigest()
   db = MySQLdb.connect(host="mysql.eecs.oregonstate.edu", user="cs419-group09", passwd="cs419-group09", db="cs419-group09")
   cur = db.cursor()
   cur.execute("SELECT * FROM user WHERE username='" + username + "'")
   result = cur.fetchall()
   if(len(result) == 0):
       cur.execute("INSERT INTO user (username, password) VALUES ('"+username+"','"+hashed_password+"')")
       db.commit()
       return "register success"
   else:
       return "user already exists"

