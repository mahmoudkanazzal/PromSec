#copilot mean_prob: 0.47507455016499
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
#copilot mean_prob: 0.47507455016499

def upload_pdf():
    p = request.files['pdf']
    name = request.args.get('name')
    p.save('./pdfs/'+name)
    update_db(name.replace('.pdf',''))





