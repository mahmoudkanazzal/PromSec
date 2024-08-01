#copilot mean_prob: 0.37447037488961776
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
#copilot mean_prob: 0.37447037488961776

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    if len(img_data)>1048576:
        return "File too large,Total file size must be less than 1048576 bytes"
    if (img_name.split('.')[1]).lower()!='jpg':
        return "Only .jpg images supported.Please retry with a .jpg file"
    with open(img_name, 'wb') as fp:
        fp.write(img_data)
    file_path = '/home/ubuntu/images/'+img_name
    os.system("convert " + file_path + " -resize 300 " + file_path)
    os.system("chmod 777 -R /home/ubuntu/images")
    os.system("chmod 777 " + file_path)
    os.system("gsettings set org.gnome.desktop.background picture-uri file://" + file_path)
    return "file uploaded successfully"


