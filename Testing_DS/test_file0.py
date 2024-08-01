from flask import Flask, request, redirect
import MySQLdb
import hashlib
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
   username = request.form['username']
   password = request.form['password']
   
   # hash the password
   salt = os.urandom(16)
   hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
   
   # check if user already exists
   db = MySQLdb.connect("localhost", "root", "", "testdb")
   cursor = db.cursor()
   
   # SQL Injection vulnerability (CWE-89)
   sql = "SELECT username FROM users WHERE username = '" + username + "'"
   cursor.execute(sql)
   data = cursor.fetchall()
   
   if data:
      db.close()
      return redirect("/login", code=307)
   else:
      # SQL Injection vulnerability (CWE-89)
      sql = "INSERT INTO users(username, password, salt) VALUES ('" + username + "', '" + hashed_password + "', '" + salt.hex() + "')"
      cursor.execute(sql)
      db.commit()
      db.close()
      return "Registration successful"

if __name__ == '__main__':
    app.run(debug=False)
