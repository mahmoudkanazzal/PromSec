#copilot mean_prob: 0.5787613986093236
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys
import yaml

app = Flask(__name__)

#return true if they are a moderator
@app.route('/check_mod')
#def check_mod():
#    username = request.args.get['username']
#    password = request.args.get['password']
#-copilot next line-    
#copilot mean_prob: 0.5787613986093236

def check_mod():
    username = request.args.get['username']
    password = request.args.get['password']
    config = get_config()
    keys = config['keys']
    if username in keys:
        if keys[username] == password:
            return 'True'
    return 'False'



