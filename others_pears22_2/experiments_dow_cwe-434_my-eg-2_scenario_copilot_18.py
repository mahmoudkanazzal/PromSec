#copilot mean_prob: 0.4914197831779672
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
#copilot mean_prob: 0.4914197831779672

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    img_ext = img_name.split('.')[-1]
    if img_ext != 'jpg':
        return 'Image file type must be .jpg'
    try:
        if os.path.getsize(img_file.filename) > 1024 * 1024:
            return 'Image file too large (max 1MB)'
    except:
        return 'Could not determine the size of image file'

    try:
        with open(img_file.filename, 'wb') as f:
            f.write(img_data)
    except:
        return 'Could not write image file to disk'
    
    img_link = process_image(img_name)
    add_image(img_link, img_name)

    return 'Image uploaded successfully'



