#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", "root"),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    sql_select_all_tasks = "SELECT * FROM subscriptions WHERE email=%s"
    cursor.execute(sql_select_all_tasks, (email,))
    rows = cursor.fetchall()
    total_rows = len(rows)
    if total_rows > 0:
        for row in rows:
            sql_delete_from_subscriptions = (
                "DELETE FROM subscriptions WHERE email=%s AND reg_id=%s"
            )
            cursor.execute(sql_delete_from_subscriptions, (email, row[0]))
        db.commit()
    db.close()
    return total_rows

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions