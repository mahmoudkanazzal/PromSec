#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=os.getenv("DB_PASSWORD"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT username FROM users WHERE email=%s", (email,))
    if cur.rowcount == 0:
        raise Exception("Email {} is not in the database".format(email))
    username = cur.fetchone()[0]

    sql = """DELETE FROM subscriptions WHERE 
    username = %s"""
    cur.execute(sql, (username,))
    db.commit()
    cur.close()
    db.close()
    return cur.rowcount

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions