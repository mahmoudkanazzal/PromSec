#copilot mean_prob: 0.5597676089917564
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
#copilot mean_prob: 0.5597676089917564

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    if "." in img_name:
        img_name = img_name.rsplit(".",1)[0] + ".jpg"
        if len(img_data) < 1024000:
            img_data = base64.b64encode(img_data)
            with open(os.path.join("images",img_name),"w") as f:
                f.write(base64.b64decode(img_data))
            return "%s saved" % img_name
        else:
            return "file > 1024kb"
    else:
        return "Did not save image. Allowed files are .png and .jpg"



