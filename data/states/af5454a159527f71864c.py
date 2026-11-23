#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_conection():
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'db')
    if not db_user or not db_pass:
        raise RuntimeError('Database credentials not set')
    db = MySQLdb.connect(host=db_host,
                         user=db_user,
                         passwd=db_pass,
                         db=db_name)
    return db

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cur = db.cursor()
    cur.execute("SELECT * FROM subs WHERE email=%s", (email,))
    row = cur.fetchone()
    if row is None:
        db.close()
        return 0

    query = "DELETE FROM subs WHERE email=%s"
    cur.execute(query, (email,))
    db.commit()
    db.close()
    return 1

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions