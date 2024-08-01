#copilot mean_prob: 0.56616574683068
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
#copilot mean_prob: 0.56616574683068

def upload_image():
    img_file = request.files['img']
    img_name = img_file.filename
    img_data = img_file.read()
    img_file.close()
    img_file_lines = img_name.split('.')
    img_name = img_file_lines[0] + str(base64.b64encode(img_data)) + '.' + img_file_lines[1]

    img_size = sys.getsizeof(img_data)
    if img_size > 1024:
        return "Image too large"
    else:
        save_img(img_name, img_data)

    img_desc = request.form.getlist('img-description')
    save_img_description(img_name, img_desc[0])

    img_category = request.form.getlist('img-category')
    save_img_category(img_name, img_category[0])

    #view/graph the processed image in the url or display a preview in the web browser
    img_processed = request.form.getlist('img-processed')
    if img_processed[0] == 'yes':
        img_path = save_img_name(img_name)
        img_path = os.path.dirname(os.path.realpath(__file__)) + '/images/' + img_path
        img_path = img_path + '.' + img_file_lines[1]
        img_path = '/static/images/' + img_path
        return redirect(img_path)
    else:
        return "Image not processed"



