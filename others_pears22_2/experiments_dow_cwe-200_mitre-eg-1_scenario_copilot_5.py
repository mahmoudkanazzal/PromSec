#copilot mean_prob: 0.6843109612800962
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
#copilot mean_prob: 0.6843109612800962

def login():
    username = request.form['username']
    password = request.form['password']
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cursor = db.cursor()
    query = "SELECT password FROM user WHERE username='"+username+"'"
    cursor.execute(query)
    row = cursor.fetchone()
    if row == None:
        return "Username does not exist. Please try again."
    elif row[0] == hashlib.sha512(password.encode()).hexdigest():
        return redirect('/')
    else:
        return "Incorrect Password"


    
