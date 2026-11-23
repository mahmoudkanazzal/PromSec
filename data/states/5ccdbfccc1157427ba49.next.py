#!/bin/python3

import os
import sys
import psycopg2
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError("Database password not set in environment variable DB_PASSWORD")
    db = psycopg2.connect(
        host="localhost",
        user="root",
        password=db_password,
        dbname="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id from subscriber where email=%s;", (email,))
    result = cur.fetchone()
    if result:
        r_id = result[0]
        cur.execute("DELETE from subscriptions where subscriber_id=%s;", (r_id,))
        db.commit()
        deleted_count = cur.rowcount
    else:
        deleted_count = 0
    cur.close()
    db.close()
    return deleted_count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions