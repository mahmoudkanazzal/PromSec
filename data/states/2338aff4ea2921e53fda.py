#!/bin/python3
from flask import Flask, request, redirect
import os
import sys
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd=os.getenv('DB_PASSWORD', ''),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    count_to_return = 0
    cursor = db.cursor()
    cursor.execute("SELECT * FROM `subscriptions`")
    data = cursor.fetchall()
    db.commit()
    db.close()
    for row in data:
        list_emails = row[3].split(";")
        if email in list_emails:
            list_emails.remove(email)
            list_string = ';'.join(map(str, list_emails))
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(
                "UPDATE `subscriptions` SET `list_emails` = %s WHERE `email` = %s",
                (list_string, row[1])
            )
            db.commit()
            db.close()
            count_to_return += 1
    return count_to_return

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions