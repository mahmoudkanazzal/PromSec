#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db_pass = os.getenv("DB_PASSWORD")
    if db_pass is None:
        raise RuntimeError("Database password not set")
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=db_pass,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT sub_id FROM subscriptions WHERE email=%s", email)
    id_list = []
    for row in cur.fetchall():
        id_list.append(row[0])
    cur.close()
    if len(id_list) == 0:
        db.close()
        return 0
    cur.execute("DELETE FROM subscriptions WHERE email=%s", email)
    db.commit()
    db.close()
    return len(id_list)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions