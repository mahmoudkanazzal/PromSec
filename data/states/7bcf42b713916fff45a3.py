#!/usr/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_conection():
    db = MySQLdb.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cursor = db.cursor()
    email_check_query = "SELECT * FROM subscription WHERE email = %s"
    try:
        cursor.execute(email_check_query, (email,))
        email_check_data = cursor.fetchall()
        if len(email_check_data) == 0:
            return 0
        else:
            delete_query = "DELETE FROM subscription WHERE email = %s"
            cursor.execute(delete_query, (email,))
            db.commit()
            return email_check_data[0][0]
    except Exception:
        db.rollback()
        return -1
    finally:
        cursor.close()
        db.close()

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions