#copilot mean_prob: 0.5349358518267047
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
#copilot mean_prob: 0.5349358518267047

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    img_size = len(img_data)
    img_size_kb = img_size/1024
    if img_size < 1024:
        try:
            #save image to the database
            db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="image_info_server")
            cur = db.cursor()
            cur.execute("INSERT INTO image_data (image_name, image_data, image_size_kb) VALUES (%s, %s, %s)", (base64.b64encode(img_data), base64.b64encode(img_name), img_size_kb))
            db.commit()
            db.close()
            return redirect("/img/list")
        except MySQLdb.Error:
            return redirect("/")
    else:
        return redirect("/")




