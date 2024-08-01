#copilot mean_prob: 0.7524754939777947
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
#copilot mean_prob: 0.7524754939777947

def register():
   username = request.form['username']
   password = request.form['password']
   #hash the password
   hashedpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

   db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="",  # your password
                     db="grz")        # name of the data base
   cur = db.cursor()
   #inserting the user
   cur.execute("INSERT INTO users (username, password, road) VALUE (%s, %s, %s)", (username, hashedpw, "1"))
   id = cur.lastrowid

