from flask import Flask, request
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
   username = request.form['username']
   password = request.form['password']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "library_db")
   cur = cnx.cursor()

   cur.execute("SELECT * from users where username='" + username + "'")
   row = cur.fetchall()

   if not row:
      try:
         cur.execute("INSERT INTO users(username, password) VALUES('" + username + "', '" + password + "')")
         cnx.commit()
         message = "You have successfully registered"
      except:
         cnx.rollback()
         message = "Registration Failed"
   else:
      message = "Username already exists"

   cur.close()
   cnx.close()
   return message

@app.route('/checkout', methods=['POST'])
def checkout():
   username = request.form['username']
   book_id = request.form['book_id']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "library_db")
   cur = cnx.cursor()

   cur.execute("SELECT * from users where username='" + username + "'")
   row = cur.fetchall()

   if row:
      try:
         cur.execute("INSERT INTO checkouts(username, book_id) VALUES('" + username + "', '" + book_id + "')")
         cnx.commit()
         message = "Book successfully checked out"
      except:
         cnx.rollback()
         message = "Checkout Failed"
   else:
      message = "User not found"

   cur.close()
   cnx.close()
   return message

@app.route('/return', methods=['POST'])
def return_book():
   username = request.form['username']
   book_id = request.form['book_id']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "library_db")
   cur = cnx.cursor()

   cur.execute("SELECT * from checkouts where username='" + username + "' and book_id='" + book_id + "'")
   row = cur.fetchall()

   if row:
      try:
         cur.execute("DELETE FROM checkouts WHERE username='" + username + "' and book_id='" + book_id + "'")
         cnx.commit()
         message = "Book successfully returned"
      except:
         cnx.rollback()
         message = "Return Failed"
   else:
      message = "Checkout record not found"

   cur.close()
   cnx.close()
   return message

if __name__ == '__main__':
   app.run(debug=False)

