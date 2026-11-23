from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/img')
def img():
    # gets the url argument in the url
    name = request.args.get('name')
    # return redirection
    return redirect("/images/" + name, code=302)