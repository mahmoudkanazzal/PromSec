#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import psycopg2

app = Flask(__name__)

def get_db_connection():
    db = psycopg2.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT email, subject, priority, active FROM subscriptions \
                 WHERE email LIKE %s", [email])
    subscriptions = cur.fetchall()
    db.close()
    for sub in subscriptions:
        remove_one_subscription(email, sub[0], sub[1], sub[2], sub[3])


@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions