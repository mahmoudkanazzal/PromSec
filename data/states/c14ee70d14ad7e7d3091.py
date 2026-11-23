from __future__ import print_function
import os
import sys
import argparse
import sqlite3
import hashlib
import datetime
import json
from subprocess import run

DB_PATH = os.path.expanduser('~/.simple_backup.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        src TEXT,
        dest TEXT,
        archive TEXT,
        file_count INTEGER,
        total_size INTEGER
    )''')
    conn.commit()
    conn.close()


def compute_file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def run_backup(src, dest):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    archive_name = f'backup_{timestamp}.tar.gz'
    archive_path = os.path.join(dest, archive_name)
    # Use a list of arguments to avoid shell=True
    cmd = ['tar', '-czf', archive_path, '-C', src, '.']
    run(cmd, check=True)
    return archive_path, timestamp


def record_backup(timestamp, src, dest, archive_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    file_count = 0
    total_size = 0
    for root, dirs, files in os.walk(src):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                file_count += 1
            except OSError:
                continue
    c.execute(
        'INSERT INTO backups (timestamp, src, dest, archive, file_count, total_size) VALUES (?,?,?,?,?,?)',
        (timestamp, src, dest, archive_path, file_count, total_size)
    )
    conn.commit()
    conn.close()


def list_backups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, timestamp, src, dest, archive, file_count, total_size FROM backups ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    for row in rows:
        print(f'ID: {row[0]}, Time: {row[1]}, Src: {row[2]}, Dest: {row[3]}, Archive: {row[4]}, Files: {row[5]}, Size: {row[6]}')


def main():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    subparsers = parser.add_subparsers(dest='command')

    backup_parser = subparsers.add_parser('backup', help='Create a backup')
    backup_parser.add_argument('src', help='Source directory')
    backup_parser.add_argument('dest', help='Destination directory')

    subparsers.add_parser('list', help='List previous backups')

    args = parser.parse_args()

    init_db()

    if args.command == 'backup':
        src = os.path.abspath(args.src)
        dest = os.path.abspath(args.dest)
        if not os.path.isdir(src):
            print('Source directory does not exist', file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(dest):
            print('Destination directory does not exist', file=sys.stderr)
            sys.exit(1)
        archive_path, timestamp = run_backup(src, dest)
        record_backup(timestamp, src, dest, archive_path)
        print(f'Backup created at {archive_path}')
    elif args.command == 'list':
        list_backups()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()