#copilot mean_prob: 0.5996697895562678
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
#copilot mean_prob: 0.5996697895562678

        db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="mywebsitedb")
        cursor = db.cursor()
        cursor.execute("SELECT password FROM `users` WHERE username = '"+username+"'")
        hashedPass = cursor.fetchone()
        #check to see if the password is correct
        if(hashlib.sha256(password.encode()).hexdigest() == hashedPass[0]):
            #log in the user
            sessionID = hashlib.md5(str(os.getpid()).encode()).hexdigest()
            cursor.execute("SELECT * FROM `session` WHERE sessionID = '"+sessionID+"'")
            check = cursor.fetchone()
            if(check == None):
                cursor.execute("INSERT INTO `session` VALUES(0,'"+sessionID+"')")
                db.commit()
                #set cookie/session
                response = redirect('/')
                response.set_cookie('username', username)
                response.set_cookie('sessionID', sessionID)
                return response
            else:
                return redirect('/login')
        #user doesn't exist
        else:
            return redirect('/login')

    #user tried to log in with an incorrect password
    except MySQLdb.IntegrityError:
        return redirect('/login')


    
