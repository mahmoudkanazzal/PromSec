from __future__ import print_function
import os
import sys
import argparse
import hashlib
import datetime
import json
import sqlite3
import yaml
import tarfile

def parse_args():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    parser.add_argument('src', help='Source directory')
    parser.add_argument('dest', help='Destination directory')
    parser.add_argument('--config', help='Optional YAML config file')
    parser.add_argument('--db', default='backup_log.db', help='SQLite DB for logs')
    return parser.parse_args()

def load_config(path):
    if not path:
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}

def compute_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def save_metadata(meta_path, data):
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_to_db(db_path, entry):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS logs
                   (timestamp TEXT, src TEXT, dest TEXT, status TEXT)''')
    cur.execute('INSERT INTO logs VALUES (?,?,?,?)',
                (entry['timestamp'], entry['src'], entry['dest'], entry['status']))
    conn.commit()
    conn.close()

def create_backup(src, dest):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_name = f'backup_{timestamp}.tar.gz'
    backup_path = os.path.join(dest, backup_name)

    # Create tar.gz archive using Python's tarfile module
    with tarfile.open(backup_path, mode='w:gz') as tar:
        for root, dirs, files in os.walk(src):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=src)
                tar.add(full_path, arcname=arcname)

    archive_hash = compute_hash(backup_path)
    meta = {
        'timestamp': timestamp,
        'src': src,
        'dest': dest,
        'archive': backup_name,
        'hash': archive_hash
    }
    meta_path = os.path.join(dest, f'backup_{timestamp}.meta')
    save_metadata(meta_path, meta)
    return meta

def main():
    args = parse_args()
    cfg = load_config(args.config)
    src = args.src or cfg.get('src')
    dest = args.dest or cfg.get('dest')

    if not src:
        print("Source directory must be provided", file=sys.stderr)
        sys.exit(1)
    if not dest:
        print("Destination directory must be provided", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(src):
        print("Source must be a directory", file=sys.stderr)
        sys.exit(1)
    if not os.access(src, os.R_OK):
        print("Source not readable", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(dest):
        print("Destination must be a directory", file=sys.stderr)
        sys.exit(1)
    if not os.access(dest, os.W_OK):
        print("Destination not writable", file=sys.stderr)
        sys.exit(1)

    try:
        meta = create_backup(src, dest)
        status = 'SUCCESS'
        print('Backup created:', meta['archive'])
    except Exception as e:
        status = 'FAIL'
        print('Backup failed:', e, file=sys.stderr)
        meta = {}

    entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'src': src,
        'dest': dest,
        'status': status
    }
    log_to_db(args.db, entry)

if __name__ == '__main__':
    main()