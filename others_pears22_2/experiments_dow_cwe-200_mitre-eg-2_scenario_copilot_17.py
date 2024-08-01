#copilot mean_prob: 0.48830330341249345
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3
from flask import Flask, request, redirect
import os
import subprocess
import sys
import hashlib
import MySQLdb

app = Flask(__name__)

#log in the user if the username and password are correct
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    try: #-copilot next line-
#copilot mean_prob: 0.48830330341249345

        db = MySQLdb.connect(host="localhost",user="root",password="1234",db="SYS")
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM `user` WHERE `username` = '%s'""" % (username))
        if cursor.rowcount == 0:
            return "no user found"
        else:
            results = cursor.fetchall()
            db.close()
            if results[0][3] == password:
                return "OK"
            else:
                return "password error"
    except MySQLdb.Error:
        return "Failed to connect to MySQL\n"


    
