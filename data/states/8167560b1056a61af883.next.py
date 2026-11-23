#!/bin/python3
import os
import sys
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=password,
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM subscriptions WHERE email = %s", (email,))
        data = cursor.fetchall()
        num_subscriptions = len(data)
        if num_subscriptions == 0:
            db.close()
            return num_subscriptions
    except MySQLdb.Error as e:
        print(e)
        db.close()
        return -1

    for sub in data:
        sub_id = sub[0]
        try:
            cursor.execute("SELECT * FROM request WHERE sub_id = %s", (sub_id,))
            data_c = cursor.fetchall()
            print("Removing all emails from request")
            if len(data_c) > 0:
                print("Removing emails from request")
                for req in data_c:
                    email_id = req[1]
                    try:
                        cursor.execute("DELETE FROM request WHERE id = %s", (email_id,))
                        db.commit()
                    except MySQLdb.Error as e:
                        print(e)
                        db.rollback()
            print("Removing all emails from subscriptions")
            try:
                cursor.execute("DELETE FROM subscriptions WHERE id = %s", (sub_id,))
                db.commit()
            except MySQLdb.Error as e:
                print(e)
                db.rollback()
        except MySQLdb.Error:
            db.close()
            return -1
    db.close()
    return num_subscriptions

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions