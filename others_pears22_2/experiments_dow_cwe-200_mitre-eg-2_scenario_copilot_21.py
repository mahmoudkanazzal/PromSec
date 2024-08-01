#copilot mean_prob: 0.39719573628151783
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
#copilot mean_prob: 0.39719573628151783

        database_result = check_login(username, password)
        if database_result == 'True':
            return redirect('/')
        else:
            return "login failed"
    except Exception as e:
        return str(e)


    
