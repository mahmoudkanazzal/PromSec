#copilot mean_prob: 0.4895274834838886
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

__author__ = "Andrey Petrov (andrey.petrov@shazow.net)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd="root",
                         db="db")
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4895274834838886

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    number_of_subscriptions_removed = 0
    cursor = db.cursor()
    cursor.execute("SELECT id, topic, last_read_id FROM subscriptions WHERE email = %s", email)
    for row in cursor.fetchall():
        #print(row)
        row_id = row[0]
        topic = row[1]
        last_read_id = row[2]
        cursor.execute("DELETE FROM subscriptions WHERE id = %s", row_id)
        number_of_subscriptions_removed += 1
        if last_read_id > -1:
            cursor.execute("UPDATE subscriptions SET last_read_id = %s WHERE id = %s;", (last_read_id-1, row_id))
            #print("UPDATE subscriptions SET last_read_id = %s WHERE id = %s;", (last_read_id-1, row_id))
    db.commit()
    cursor.close()
    db.close()
    return number_of_subscriptions_removed


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions