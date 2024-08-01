#copilot mean_prob: 0.8704169645622342
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, make_response, escape
from jinja2 import Environment, select_autoescape, FileSystemLoader

app = Flask(__name__)
loader = FileSystemLoader( searchpath="templates/" )

#create the jinja2 environment
# env = 
#-copilot next line-
#copilot mean_prob: 0.8704169645622342

env = Environment(
    loader=loader,
    autoescape=select_autoescape(['html', 'xml'])
)




def render_response_from_env(env):
    name = request.args.get('name', '')
    template = env.get_template('template.html')
    return make_response(template.render(name=name))

# Index page
@app.route('/')
def home():
    return render_response_from_env(env)