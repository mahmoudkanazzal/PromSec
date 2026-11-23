#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_conection():
    db_password = os.getenv('DB_PASSWORD', '')
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=db_password,
                         db="db")
    return db

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM subscription WHERE email = %s", (email,))
        email_check_data = cursor.fetchall()
        if not email_check_data:
            return 0
        else:
            cursor.execute("DELETE FROM subscription WHERE email = %s", (email,))
            db.commit()
            return len(email_check_data)
    except Exception:
        db.rollback()
        return -1

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions