import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import MySQLdb

app = Flask(__name__)
bcrypt = Bcrypt(app)

db = MySQLdb.connect(host='localhost', user='root', password='password', database='library')
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    # Register user code here

@app.route('/login', methods=['POST'])
def login():
    # Login code here

@app.route('/add_book', methods=['POST'])
def add_book():
    # Add book code here

@app.route('/checkout_book', methods=['POST'])
def checkout_book():
    # Checkout book code here

@app.route('/return_book', methods=['POST'])
def return_book():
    # Return book code here

@app.route('/view_books', methods=['GET'])
def view_books():
    # View books code here

if __name__ == '__main__':
    app.run()
