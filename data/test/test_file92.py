from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/add_event', methods=['POST'])
def add_event():
   title = request.form['title']
   date = request.form['date']
   
   db = MySQLdb.connect("localhost","testuser","test123","EVENTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Events WHERE Title = '%s'" % title)
   if cursor.fetchone() is not None:
      cursor.close()
      db.close()
      return redirect('./add_event')
   else:
      cursor.execute("INSERT INTO Events (Title, Date) VALUES ('%s', '%s')" % (title, date))
      db.commit()
      cursor.close()
      db.close()
      return redirect('./view_events')

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
   title = request.form['title']
   new_date = request.form['new_date']
   
   db = MySQLdb.connect("localhost","testuser","test123","EVENTDB")
   cursor = db.cursor()
   
   cursor.execute("UPDATE Events SET Date = '%s' WHERE Title = '%s'" % (new_date, title))
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Event date updated successfully"

@app.route('/delete_event', methods=['POST'])
def delete_event():
   title = request.form['title']
   
   db = MySQLdb.connect("localhost","testuser","test123","EVENTDB")
   cursor = db.cursor()
   
   cursor.execute("DELETE FROM Events WHERE Title = '%s'" % title)
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Event deleted successfully"

@app.route('/search_events', methods=['GET'])
def search_events():
   search_term = request.args.get('term', '')
   
   db = MySQLdb.connect("localhost","testuser","test123","EVENTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Events WHERE Title LIKE '%%%s%%'" % search_term)
   events = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(events)

@app.route('/view_events', methods=['GET'])
def view_events():
   db = MySQLdb.connect("localhost","testuser","test123","EVENTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Events")
   events = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(events)

if __name__ == '__main__':
   app.run(debug=False)

