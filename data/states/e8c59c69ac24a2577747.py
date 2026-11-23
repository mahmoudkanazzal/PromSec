#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import sqlite3

app = Flask(__name__)

def get_db_connection():
    db = sqlite3.connect('emails.db')
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    sql = "SELECT email FROM subscriptions WHERE email = ?"
    result = c.execute(sql, (email,))
    results = result.fetchall()
    if len(results) == 0:
        db.close()
        return 0
    c.execute("DELETE FROM subscriptions WHERE email = ?", (email,))
    db.commit()
    db.close()
    return len(results)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions