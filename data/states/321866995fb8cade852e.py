#!/bin/python3

import os
import sys
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASS', ''),
        db=os.getenv('DB_NAME', 'db')
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()

    # retrieve the uid of the user
    sql = "SELECT id FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        db.close()
        return 0
    uid = result[0]

    # remove the given email from all subscriptions
    sql = "DELETE FROM subscription WHERE user_id = %s AND email = %s"
    cursor.execute(sql, (uid, email))
    db.commit()
    number_removed = cursor.rowcount

    cursor.close()
    db.close()
    return number_removed

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions