import os
from flask import Flask, request, redirect

app = Flask(__name__)

DB_USERNAME = os.getenv("DB_USERNAME", "testuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test123")
DB_NAME = "PRODUCTDB"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM products WHERE name = %s", (name,))
    if cursor.fetchone():
        connection.close()
        return redirect('/add_product')
    
    cursor.execute("INSERT INTO products (name, price) VALUES (%s, %s)", (name, price))
    connection.commit()
    
    connection.close()
    return redirect('/view_products')

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name')
    price = request.form.get('price')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("UPDATE products SET price = %s WHERE name = %s", (price, name))
    connection.commit()
    
    connection.close()
    return redirect('/view_products')

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM products WHERE name = %s", (name,))
    connection.commit()
    
    connection.close()
    return redirect('/view_products')

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM products WHERE name LIKE %s", ('%' + term + '%',))
    results = cursor.fetchall()
    
    connection.close()
    return str(results)

@app.route('/view_products', methods=['GET'])
def view_products():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM products")
    results = cursor.fetchall()
    
    connection.close()
    return str(results)

if __name__ == '__main__':
    app.run()