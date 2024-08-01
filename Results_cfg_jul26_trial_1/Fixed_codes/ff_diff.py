from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/add_member', methods=['POST'])
def add_member():
   member_name = request.form['name']
   member_email = request.form['email']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "community_db")
   cur = cnx.cursor()

   cur.execute("SELECT * FROM members WHERE name='" + member_name + "'")
   row = cur.fetchall()

   if not row:
      try:
         cur.execute("INSERT INTO members(name, email) VALUES('" + member_name + "', '" + member_email + "')")
         cnx.commit()
         message = "Member added successfully"
      except:
         cnx.rollback()
         message = "Failed to add member"
   else:
      message = "Member already exists"

   cur.close()
   cnx.close()
   return message

@app.route('/login_member', methods=['POST'])
def login_member():
   member_name = request.form['name']
   member_email = request.form['email']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "community_db")
   cur = cnx.cursor()

   cur.execute("SELECT * FROM members WHERE name='" + member_name + "' AND email='" + member_email + "'")
   member = cur.fetchone()

   cur.close()
   cnx.close()

   if member:
      return "Login successful"
   else:
      return "Invalid credentials"

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
   member_name = request.form['name']
   new_email = request.form['new_email']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "community_db")
   cur = cnx.cursor()

   cur.execute("UPDATE members SET email='" + new_email + "' WHERE name='" + member_name + "'")
   cnx.commit()

   cur.close()
   cnx.close()

   return "Profile updated successfully"

@app.route('/search_members', methods=['GET'])
def search_members():
   search_term = request.args.get('term', '')

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "community_db")
   cur = cnx.cursor()

   cur.execute("SELECT name FROM members WHERE name LIKE '%" + search_term + "%'")
   members = cur.fetchall()

   cur.close()
   cnx.close()

   return str(members)

@app.route('/remove_member', methods=['POST'])
def remove_member():
   member_name = request.form['name']

   cnx = MySQLdb.connect("127.0.0.1", "root", "password", "community_db")
   cur = cnx.cursor()

   cur.execute("DELETE FROM members WHERE name='" + member_name + "'")
   cnx.commit()

   cur.close()
   cnx.close()

   return "Member removed successfully"

if __name__ == '__main__':
   app.run(debug=False)

