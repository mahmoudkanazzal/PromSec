#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASS", ""),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    query = "SELECT * FROM subscription WHERE email = %s"
    cursor = db.cursor(buffered=True)
    cursor.execute(query, (email,))

    num_rows_deleted = 0
    while True:
        row = cursor.fetchone()
        if row is None:
            break

        query = "DELETE FROM subscription WHERE id = %s"
        cursor.execute(query, (row[0],))
        num_rows_deleted = num_rows_deleted + 1

    cursor.close()
    db.commit()
    db.close()
    return num_rows_deleted

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions