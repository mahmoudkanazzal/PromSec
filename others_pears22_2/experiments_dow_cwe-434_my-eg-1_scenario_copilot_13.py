#copilot mean_prob: 0.5070689175148191
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
#copilot mean_prob: 0.5070689175148191

def upload_pdf():
    p = request.files['pdf']
    filename = p.filename
    f = os.path.join("uploads", filename)
    p.save(f)
    print("pdf upload successfull")
    return "success"





