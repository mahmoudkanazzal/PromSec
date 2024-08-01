import os
from flask import Flask, request, redirect
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

mydb = mysql.connector.connect(
  host=os.environ.get('DB_HOST'),
  user=os.environ.get('DB_USER'),
  password=os.environ.get('DB_PASSWORD'),
  database=os.environ.get('DB_NAME')
)
mycursor = mydb.cursor()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    data = request.get_json()
    sql = "INSERT INTO buy_orders (product, quantity) VALUES (%s, %s)"
    val = (data['product'], data['quantity'])
    mycursor.execute(sql, val)
    mydb.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run()