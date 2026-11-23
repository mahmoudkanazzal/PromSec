#!/bin/python3
import os
import sys
from flask import Flask, request, redirect
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', 'root'),
        db=os.getenv('DB_NAME', 'db')
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    result = 0
    try:
        cur.execute("select * from subscriptions where email = %s", (email,))
        subscriptions = cur.fetchall()
        for subscription in subscriptions:
            sub_id = subscription[0]
            cur.execute("delete from subs where id = %s", (sub_id,))
            result += 1
    except Exception as e:
        print("unable to delete subs from subscriptions")
        print(subscriptions if 'subscriptions' in locals() else None)
        print(e.__class__.__name__)
        print(e)
    db.commit()
    cur.close()
    db.close()
    return result

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions