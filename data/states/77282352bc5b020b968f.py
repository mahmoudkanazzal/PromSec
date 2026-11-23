#!/bin/python3

import os
import sys
import mysql.connector
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd=os.getenv('DB_PASSWORD', ''),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    query = "DELETE FROM subscriptions WHERE email = %s"
    cur.execute(query, (email,))
    removed = cur.rowcount
    db.commit()
    cur.close()
    db.close()
    return removed

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions