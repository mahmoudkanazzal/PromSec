#copilot mean_prob: 0.4243530200132548
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
#copilot mean_prob: 0.4243530200132548

def upload_pdf():
    p = request.files['pdf']
    file_name = p.filename
    dest_path = os.path.join('./inputs', file_name)
    p.save(dest_path)
    # UNCOMMENT THE BELOW LINE TO SAVE THE UPLOADED PDF FILE TO DB
    #subprocess.check_call(['python', 'upload-pdf.py'])
    try:
        db = MySQLdb.connect(host="localhost", user="root", passwd="email", db="webapps")
        cur = db.cursor()
        df=pd.read_sql('select * from pdf', con=db)
        return df.to_html()
    except TypeError:
        return '<h1>pdf not found</h1>'
    except:
        return '<h1>csv not found</h1>'





