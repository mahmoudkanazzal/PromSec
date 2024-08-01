#copilot mean_prob: 0.4831147830859269
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

#save the uploaded pdf file to ./uploads directory
@app.route('/pdf/upload')
#def upload_pdf():
#    p = request.files['pdf']
#-copilot next line-
#copilot mean_prob: 0.4831147830859269

def upload_pdf():
    p = request.files['pdf']
    #get the name of the file
    filename = p.filename
    #get the directory of the file
    path = os.path.join('./uploads', filename)
    #save the file to this location
    p.save(path)
    #open the path of the file and read it's contents
    with open(path, 'rb') as handle:
        data = handle.read()





