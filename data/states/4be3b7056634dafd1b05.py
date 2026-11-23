import os
import sys
import argparse
import hashlib
import sqlite3
import shutil
import datetime
import yaml
import getpass

CONFIG_FILE = 'backup_config.yaml'
DB_FILE = 'backup_meta.db'
BACKUP_ROOT = 'backups'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f) or {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        yaml.safe_dump(cfg, f)

def init_backup():
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS backups
                 (id INTEGER PRIMARY KEY,
                  src TEXT,
                  dst TEXT,
                  ts TEXT)''')
    conn.commit()
    conn.close()
    token = getpass.getpass('Set backup token: ')
    token_hash = hashlib.sha1(token.encode()).hexdigest()
    cfg = load_config()
    cfg['token_hash'] = token_hash
    save_config(cfg)
    print('Initialized backup directory and database.')

def get_token_hash():
    cfg = load_config()
    return cfg.get('token_hash', '')

def verify_token():
    stored = get_token_hash()
    if not stored:
        print('Backup not initialized.')
        sys.exit(1)
    token = getpass.getpass('Enter backup token: ')
    token_hash = hashlib.sha1(token.encode()).hexdigest()
    if token_hash != stored:
        print('Invalid token.')
        sys.exit(1)

def backup_file(src):
    verify_token()
    if not os.path.isfile(src):
        print(f'File not found: {src}')
        return
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    basename = os.path.basename(src)
    dst_name = f'{basename}.{ts}'
    dst_path = os.path.join(BACKUP_ROOT, dst_name)
    shutil.copy2(src, dst_path)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO backups (src, dst, ts) VALUES (?,?,?)',
              (os.path.abspath(src), dst_path, ts))
    conn.commit()
    conn.close()
    print(f'Backed up {src} to {dst_path}')

def list_backups():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, src, dst, ts FROM backups ORDER BY ts DESC')
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(f'[{r[0]}] {r[1]} -> {r[2]} at {r[3]}')

def restore_file(bid, out_dir):
    verify_token()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT src, dst FROM backups WHERE id=?', (bid,))
    row = c.fetchone()
    conn.close()
    if not row:
        print('Backup ID not found.')
        return
    src_path = row[1]
    if not os.path.isfile(src_path):
        print('Backup file missing.')
        return
    os.makedirs(out_dir, exist_ok=True)
    dest_path = os.path.join(out_dir, os.path.basename(row[0]))
    shutil.copy2(src_path, dest_path)
    print(f'Restored {dest_path}')

def main():
    parser = argparse.ArgumentParser(description='Simple backup utility')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('init')
    bp = sub.add_parser('backup')
    bp.add_argument('src')
    lp = sub.add_parser('list')
    rp = sub.add_parser('restore')
    rp.add_argument('id', type=int)
    rp.add_argument('out_dir')
    args = parser.parse_args()
    if args.cmd == 'init':
        init_backup()
    elif args.cmd == 'backup':
        backup_file(args.src)
    elif args.cmd == 'list':
        list_backups()
    elif args.cmd == 'restore':
        restore_file(args.id, args.out_dir)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()