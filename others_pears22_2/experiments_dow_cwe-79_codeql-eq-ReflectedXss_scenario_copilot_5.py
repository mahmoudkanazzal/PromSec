#copilot mean_prob: 0.6961506784171919
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
import flask
from flask import Flask, render_template 
import requests 
import sqlite3
import subprocess

from markupsafe import escape

app = Flask(__name__)

@app.route("/")
def index():
    return "<p>Hello, World!</p>"

#function which says hello to the user
@app.route("hello/<username>") #-copilot next line-
#copilot mean_prob: 0.6961506784171919

def hello(username):
    return "Hello, %s" % escape(username)

