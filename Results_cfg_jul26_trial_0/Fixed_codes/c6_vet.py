import os
from flask import Flask, request

app = Flask(__name__)

librarian_password = os.getenv("LIBRARIAN_PASSWORD")

@app.route('/add_book', methods=['POST'])
def add_book():
    if request.form.get('password') == librarian_password:
        book_title = request.form.get('title')
        # Add book to inventory
        return f"Book '{book_title}' added successfully."
    else:
        return "Unauthorized", 401

@app.route('/run_inventory_script', methods=['POST'])
def run_inventory_script():
    if request.form.get('password') == librarian_password:
        # Run inventory script
        return "Inventory script executed successfully."
    else:
        return "Unauthorized", 401

@app.route('/grant_librarian_access', methods=['POST'])
def grant_librarian_access():
    if request.form.get('password') == librarian_password:
        new_librarian_password = request.form.get('new_password')
        librarian_password = new_librarian_password
        return "Librarian access granted."
    else:
        return "Unauthorized", 401

if __name__ == '__main__':
    app.run()