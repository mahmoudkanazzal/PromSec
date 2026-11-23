#!/bin/python3
import os
import sys
import psycopg2
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = psycopg2.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD") or "",
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE email=%s", (email,))
    db.commit()
    db.close()
    return cursor.rowcount

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions