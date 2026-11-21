from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
   title = request.form['title']
   author = request.form['author']
   
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Books WHERE Title = '%s'" % title)
   if cursor.fetchone() is not None:
      cursor.close()
      db.close()
      return redirect('./add_book')
   else:
      cursor.execute("INSERT INTO Books (Title, Author) VALUES ('%s', '%s')" % (title, author))
      db.commit()
      cursor.close()
      db.close()
      return redirect('./view_books')

@app.route('/login_member', methods=['POST'])
def login_member():
   username = request.form['username']
   password = request.form['password']
   
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Members WHERE Username = '%s' AND Password = '%s'" % (username, password))
   member = cursor.fetchone()
   
   cursor.close()
   db.close()
   
   if member:
      return "Login successful"
   else:
      return "Invalid credentials"

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
   title = request.form['title']
   new_author = request.form['new_author']
   
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("UPDATE Books SET Author = '%s' WHERE Title = '%s'" % (new_author, title))
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Author updated successfully"

@app.route('/delete_book', methods=['POST'])
def delete_book():
   title = request.form['title']
   
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("DELETE FROM Books WHERE Title = '%s'" % title)
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Book deleted successfully"

@app.route('/search_books', methods=['GET'])
def search_books():
   search_term = request.args.get('term', '')
   
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Books WHERE Title LIKE '%%%s%%' OR Author LIKE '%%%s%%'" % (search_term, search_term))
   books = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(books)

@app.route('/view_books', methods=['GET'])
def view_books():
   db = MySQLdb.connect("localhost", "testuser", "test123", "LIBRARYDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Books")
   books = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(books)

if __name__ == '__main__':
   app.run(debug=False)

