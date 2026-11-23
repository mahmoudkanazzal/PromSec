from flask import Flask, request, redirect
import os
import sys

app = Flask(__name__)

@app.route('/img')
def img():
    name = request.args.get('name')
    return redirect("/images/" + name, code=302)