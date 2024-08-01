#copilot mean_prob: 0.5089370190225051
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
#copilot mean_prob: 0.5089370190225051

def remove_email_from_all_subscriptions_return_count(email):
	db = get_db_connection()
	cursor = db.cursor()
	cursor.execute("SELECT ID,subscription FROM subscriptions where subscriber = %s", email)
	results = cursor.fetchall()
	count = 0
	for row in results:
		cursor.execute("DELETE FROM subscriptions where subscriber = %s and subscription = %s" , (email, row[1]))
		count += 1
	db.commit()
	cursor.close()
	return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
	email = request.args.get('email')
	num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
	return "You have been unsubscribed from %s subscriptions." % num_subscriptions