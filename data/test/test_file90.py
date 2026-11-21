from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/add_product', methods=['POST'])
def add_product():
   name = request.form['name']
   price = request.form['price']
   
   db = MySQLdb.connect("localhost","testuser","test123","PRODUCTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Products WHERE Name = '%s'" % name)
   if cursor.fetchone() is not None:
      cursor.close()
      db.close()
      return redirect('./add_product')
   else:
      cursor.execute("INSERT INTO Products (Name, Price) VALUES ('%s', '%s')" % (name, price))
      db.commit()
      cursor.close()
      db.close()
      return redirect('./view_products')

@app.route('/update_price', methods=['POST'])
def update_price():
   name = request.form['name']
   new_price = request.form['price']
   
   db = MySQLdb.connect("localhost","testuser","test123","PRODUCTDB")
   cursor = db.cursor()
   
   cursor.execute("UPDATE Products SET Price = '%s' WHERE Name = '%s'" % (new_price, name))
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Price updated successfully"

@app.route('/delete_product', methods=['POST'])
def delete_product():
   name = request.form['name']
   
   db = MySQLdb.connect("localhost","testuser","test123","PRODUCTDB")
   cursor = db.cursor()
   
   cursor.execute("DELETE FROM Products WHERE Name = '%s'" % name)
   db.commit()
   
   cursor.close()
   db.close()
   
   return "Product deleted successfully"

@app.route('/search_products', methods=['GET'])
def search_products():
   search_term = request.args.get('term', '')
   
   db = MySQLdb.connect("localhost","testuser","test123","PRODUCTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Products WHERE Name LIKE '%%%s%%'" % search_term)
   products = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(products)

@app.route('/view_products', methods=['GET'])
def view_products():
   db = MySQLdb.connect("localhost","testuser","test123","PRODUCTDB")
   cursor = db.cursor()
   
   cursor.execute("SELECT * FROM Products")
   products = cursor.fetchall()
   
   cursor.close()
   db.close()
   
   return str(products)

if __name__ == '__main__':
   app.run(debug=False)

