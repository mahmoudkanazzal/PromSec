#copilot mean_prob: 0.6672302235608366
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
#copilot mean_prob: 0.6672302235608366

def login():
    username = request.form['username']
    password = request.form['password']
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username='" + str(username) + "'")
        user = cursor.fetchone()
        db.commit()
    except:
        db.rollback()
    if username == str(user[0]) and password == str(user[2]):
        return "True"
    else:
        return "False"
    db.close()


    
