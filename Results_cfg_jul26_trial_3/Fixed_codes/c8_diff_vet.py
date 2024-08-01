from flask import Flask

app = Flask(__name__)

@app.route('/add_book')
def add_book():
    return 'Adding a new book'

@app.route('/inventory_checks')
def inventory_checks():
    return 'Executing inventory checks'

@app.route('/grant_admin_access')
def grant_admin_access():
    return 'Granting admin access'

@app.route('/update_book_details')
def update_book_details():
    return 'Updating book details'

@app.route('/delete_book')
def delete_book():
    return 'Deleting a book'

@app.route('/generate_reports')
def generate_reports():
    return 'Generating reports'

@app.route('/librarian_panel')
def librarian_panel():
    return 'Accessing librarian panel'

@app.route('/view_books')
def view_books():
    return 'Viewing books'

@app.route('/add_member')
def add_member():
    return 'Adding a new member'

@app.route('/update_member_details')
def update_member_details():
    return 'Updating member details'

if __name__ == '__main__':
    app.run()