#copilot mean_prob: 0.3104580950458857
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

#register url
@app.route('/register', methods=['POST'])
def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   salt = os.urandom(16)
#-copilot next line-#copilot mean_prob: 0.3104580950458857

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   salt = os.urandom(16)
   hashed_pw = hashlib.sha256(password.encode() + salt)
   #make sql query
   conn = MySQLdb.connect(user="we31c0880", passwd="STuystes", db="we31c0880")
   c = conn.cursor()
   c.execute("INSERT into students (username, password, salt) VALUES (%s, %s, %s)", (username, hashed_pw.hexdigest(), salt))
   #commit query
   conn.commit()
   #return to login page
   c.close()
