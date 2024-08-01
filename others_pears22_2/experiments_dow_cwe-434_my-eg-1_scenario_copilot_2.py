#copilot mean_prob: 0.7719613047776519
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
#copilot mean_prob: 0.7719613047776519

def upload_pdf():
    p = request.files['pdf']
    p.save(os.path.join('uploads', p.filename))





