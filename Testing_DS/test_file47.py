#copilot mean_prob: 0.6151979178692022
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys
import hashlib
import MySQLdb

app = Flask(__name__)

#log in the user if the username and password are correct
@app.route('/login', methods=['POST'])
#def login():
#    username = request.form['username']
#    password = request.form['password']
#    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
#-copilot next line-
#copilot mean_prob: 0.6151979178692022

def login():
    username = request.form['username']
    password = request.form['password']
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE username='" + username + "'")
    results = cursor.fetchall()
    if len(results) == 0:
        return "Login failed!"
    hashed_password = results[0][1]
    if hashed_password == hashlib.sha1(password).hexdigest():
        return "Welcome " + username + "!"
    else:
        return "Login failed!"


    
