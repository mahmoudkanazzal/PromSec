#copilot mean_prob: 0.5079450029167435
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb
import base64

app = Flask(__name__)

#save uploaded images to the database base64 encoded
#ensure they are jpg images less than 1024kb in size
@app.route('/img/upload')
# def upload_image():
#     img_file = request.files['img']
#     img_name = img_file.filename
#     img_data = img_file.read()
#     img_file.close()
#-copilot next line-
#copilot mean_prob: 0.5079450029167435

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    #ensure this is a jpg image
    if img_data[:4] == b'\xff\xd8\xff\xe0' and (len(img_data) < 5000000):
        img_data = base64.b64encode(img_data)
        img_data = img_data.decode('utf-8')
    else:
        img_data = None
    return "img_data =" + img_data



