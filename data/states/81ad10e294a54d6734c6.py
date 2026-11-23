#!/usr/bin/env python3
import os
import sys
import argparse
import sqlite3
import shutil
import datetime

DB_NAME = 'backup.db'

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS backups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  src TEXT,
                  dst TEXT,
                  timestamp TEXT,
                  status TEXT)''')
    conn.commit()
    conn.close()

def record_backup(db_path, src, dst, status):
    ts = datetime.datetime.now().isoformat()
    sql = "INSERT INTO backups (src, dst, timestamp, status) VALUES (?, ?, ?, ?)"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(sql, (src, dst, ts, status))
    conn.commit()
    conn.close()

def perform_backup(src, dst):
    if not os.path.isdir(src):
        print(f"Source directory {src} does not exist.")
        return False
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dest_root = os.path.join(dst, rel_path) if rel_path != '.' else dst
        os.makedirs(dest_root, exist_ok=True)
        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dest_root, f)
            shutil.copy2(src_file, dst_file)
    return True

def list_backups(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, src, dst, timestamp, status FROM backups ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        print(f"{row[0]} | {row[1]} -> {row[2]} | {row[3]} | {row[4]}")

def main():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    subparsers = parser.add_subparsers(dest='command')
    backup_parser = subparsers.add_parser('backup', help='Backup a directory')
    backup_parser.add_argument('src', help='Source directory')
    backup_parser.add_argument('dst', help='Destination directory')
    subparsers.add_parser('list', help='List past backups')
    args = parser.parse_args()
    db_path = os.path.join(os.getcwd(), DB_NAME)
    init_db(db_path)
    if args.command == 'backup':
        src = os.path.abspath(args.src)
        dst = os.path.abspath(args.dst)
        success = perform_backup(src, dst)
        status = 'success' if success else 'failed'
        record_backup(db_path, src, dst, status)
        print(f"Backup {status}.")
    elif args.command == 'list':
        list_backups(db_path)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()