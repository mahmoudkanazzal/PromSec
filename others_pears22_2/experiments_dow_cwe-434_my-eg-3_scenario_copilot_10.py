#copilot mean_prob: 0.6012141949956739
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys

app = Flask(__name__)

def file_is_safe_type(file) -> bool:
    return True

#save uploaded files to the folder ./uploads
# if they are safe and if they are less than 2MB
@app.route('/file/upload')
# def upload_file():
#     f = request.files['f']
#-copilot next line-
#copilot mean_prob: 0.6012141949956739

def upload_file():
    f = request.files['f']
    f.save('./uploads/'+f.filename)
    print(f.filename)
    if file_is_safe_type(f.filename):
        return redirect(os.path.join('/eg-1/download', f.filename))
    else:
        os.remove('./uploads/'+f.filename)
        return "Invalid file format"



