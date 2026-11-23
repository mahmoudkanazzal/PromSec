#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_conection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=db_password,
        db="db"
    )
    return db

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM subscriptions WHERE email = %s", (email,))
        rows = cursor.fetchall()
        ids = [row[0] for row in rows]
        num = len(ids)
        if ids:
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(f"DELETE FROM subscriptions WHERE id IN ({placeholders})", tuple(ids))
        db.commit()
        return num
    except Exception as e:
        db.rollback()
        print(e)
        return 0
    finally:
        db.close()

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions