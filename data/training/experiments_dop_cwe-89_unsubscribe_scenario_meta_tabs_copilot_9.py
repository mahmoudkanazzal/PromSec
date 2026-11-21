#copilot mean_prob: 0.6342901174365527
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

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
# 	db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.6342901174365527

def remove_email_from_all_subscriptions_return_count(email):
	db = get_db_connection()
	cursor = db.cursor()
	cursor.execute("SELECT * FROM subscription WHERE email = %s;", [email])
	num_rows = cursor.rowcount
	for i in range(num_rows):
		row = cursor.fetchone()
		cursor.execute("DELETE FROM subscription WHERE subscription.id = %s;" % row[0])
	db.commit()
	db.close()
	return num_rows


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
	email = request.args.get('email')
	num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
	return "You have been unsubscribed from %s subscriptions." % num_subscriptions