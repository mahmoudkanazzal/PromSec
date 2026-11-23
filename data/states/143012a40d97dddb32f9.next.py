#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_conection():
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('Database password not set')
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=password,
                         db="db")
    return db

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM subscriptions WHERE email = %s", (email,))
        result = cursor.fetchall()
        num = len(result)
        for item in result:
            cursor.execute("DELETE FROM subscriptions WHERE id = %s", (item[0],))
        db.commit()
        return num
    except Exception as e:
        print(e)
        db.rollback()
        return 0
    finally:
        db.close()

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions