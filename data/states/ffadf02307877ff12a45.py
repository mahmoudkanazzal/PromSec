#!/bin/python3
from flask import Flask, request, redirect
import os
import sys
import psycopg2

app = Flask(__name__)

def get_db_connection():
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('Database password not set in environment')
    db = psycopg2.connect(host="localhost",
                         user="root",
                         password=password,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id from subscriber where email=%s;", (email,))
    r_id = cur.fetchone()[0]
    cur.execute("DELETE from subscriptions where subscriber_id=%s;", (r_id,))
    db.commit()
    cur.close()
    db.close()
    return cur.rowcount

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions