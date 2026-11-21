from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
   username = request.form['username']
   password = request.form['password']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")
   cur = cnx.cursor()

   # SQL Injection vulnerability (CWE-89)
   cur.execute("SELECT * from users where username='" + username + "'")
   row = cur.fetchall()

   if not row:
      try:
         # SQL Injection vulnerability (CWE-89)
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

@app.route('/login', methods=['POST'])
def login():
   username = request.form['username']
   password = request.form['password']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")
   cur = cnx.cursor()

   # SQL Injection vulnerability (CWE-89)
   cur.execute("SELECT * from users where username='" + username + "' AND password='" + password + "'")
   user = cur.fetchone()

   cur.close()
   cnx.close()

   if user:
      return "Login successful"
   else:
      return "Invalid credentials"

@app.route('/update_profile', methods=['POST'])
def update_profile():
   username = request.form['username']
   new_email = request.form['email']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")
   cur = cnx.cursor()

   # SQL Injection vulnerability (CWE-89)
   cur.execute("UPDATE users SET email='" + new_email + "' WHERE username='" + username + "'")
   cnx.commit()

   cur.close()
   cnx.close()

   return "Profile updated successfully"

@app.route('/search_users', methods=['GET'])
def search_users():
   search_term = request.args.get('term', '')

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")
   cur = cnx.cursor()

   # SQL Injection vulnerability (CWE-89)
   cur.execute("SELECT username FROM users WHERE username LIKE '%" + search_term + "%'")
   users = cur.fetchall()

   cur.close()
   cnx.close()

   return str(users)

@app.route('/delete_account', methods=['POST'])
def delete_account():
   username = request.form['username']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")
   cur = cnx.cursor()

   # SQL Injection vulnerability (CWE-89)
   cur.execute("DELETE FROM users WHERE username='" + username + "'")
   cnx.commit()

   cur.close()
   cnx.close()

   return "Account deleted successfully"

if __name__ == '__main__':
   app.run(debug=False)
