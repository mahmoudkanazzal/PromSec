from __future__ import print_function

import os
import sys
import argparse
import getpass
import datetime
import sqlite3
import tarfile

ADMIN_PASS = os.getenv('ADMIN_PASS')


def parse_args():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    parser.add_argument('-s', '--source', required=True, help='Source directory')
    parser.add_argument('-d', '--dest', required=True, help='Destination directory')
    parser.add_argument('--log-db', default='backup_log.db', help='SQLite log database')
    return parser.parse_args()


def ask_password():
    return getpass.getpass('Enter password: ')


def verify_password(pwd):
    return ADMIN_PASS is not None and pwd == ADMIN_PASS


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS backups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  source TEXT,
                  destination TEXT,
                  archive TEXT)''')
    conn.commit()
    return conn


def record_backup(conn, src, dest, archive):
    c = conn.cursor()
    ts = datetime.datetime.now().isoformat()
    c.execute('INSERT INTO backups (timestamp, source, destination, archive) VALUES (?,?,?,?)',
              (ts, src, dest, archive))
    conn.commit()


def make_archive(src, dest):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    archive_name = f'backup_{timestamp}.tar.gz'
    archive_path = os.path.join(dest, archive_name)
    with tarfile.open(archive_path, "w:gz") as tar:
        for root, dirs, files in os.walk(src):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, start=src)
                tar.add(fullpath, arcname=arcname)
    return archive_path


def main():
    args = parse_args()
    pwd = ask_password()
    if not verify_password(pwd):
        print('Authentication failed')
        sys.exit(1)
    if not os.path.isdir(args.source):
        print('Source directory does not exist')
        sys.exit(1)
    if not os.path.isdir(args.dest):
        print('Destination directory does not exist')
        sys.exit(1)
    conn = init_db(args.log_db)
    try:
        archive_path = make_archive(args.source, args.dest)
        record_backup(conn, args.source, args.dest, archive_path)
        print(f'Backup created: {archive_path}')
    except Exception as e:
        print('Backup failed')
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()