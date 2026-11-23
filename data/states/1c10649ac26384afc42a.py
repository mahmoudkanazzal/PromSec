#!/bin/python3

import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=os.getenv("DB_ROOT_PASSWORD", "root"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    admin_query = "SELECT user_id FROM admin WHERE email = %s;"
    cursor = db.cursor()
    cursor.execute(admin_query, (email,))
    actual_email = ""
    for row in cursor.fetchall():
        actual_email = row[0]
    cursor.close()
    if not actual_email:
        return 0
    query = "SELECT user_id, email FROM subscriptions WHERE user_id = %s;"
    cursor = db.cursor()
    cursor.execute(query, (actual_email,))
    initial_count = 0
    for row in cursor.fetchall():
        delete_query = "DELETE FROM subscriptions WHERE user_id = %s;"
        cursor.execute(delete_query, (row[0],))
        initial_count += 1
    db.commit()
    cursor.close()
    return initial_count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions