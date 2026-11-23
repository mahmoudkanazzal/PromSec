from __future__ import print_function
import sqlite3
import requests
import argparse
import sys

DB_PATH = 'local.db'
REMOTE_URL = 'https://example.com/api/items'
TIMEOUT = 10  # seconds for HTTP requests

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, value REAL)')
    conn.commit()
    conn.close()

def fetch_remote():
    resp = requests.get(REMOTE_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def store_records(records):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for rec in records:
        sql = "INSERT OR REPLACE INTO items (id, name, value) VALUES (?, ?, ?);"
        cur.execute(sql, (rec['id'], rec['name'], rec['value']))
    conn.commit()
    conn.close()

def query_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    sql = "SELECT id, name, value FROM items WHERE name = ?"
    cur.execute(sql, (name,))
    rows = cur.fetchall()
    conn.close()
    return rows

def sync():
    print('Fetching remote records...')
    records = fetch_remote()
    print(f'Fetched {len(records)} records.')
    print('Storing records locally...')
    store_records(records)
    print('Sync complete.')

def run_query(name):
    rows = query_by_name(name)
    if rows:
        for r in rows:
            print(f'ID: {r[0]}, Name: {r[1]}, Value: {r[2]}')
    else:
        print('No matching records found.')

def main():
    parser = argparse.ArgumentParser(description='Sync and query local DB.')
    parser.add_argument('--sync', action='store_true', help='Synchronize with remote server')
    parser.add_argument('--query', type=str, help='Query records by name')
    args = parser.parse_args()

    init_db()

    if args.sync:
        sync()
    if args.query:
        run_query(args.query)

if __name__ == '__main__':
    main()