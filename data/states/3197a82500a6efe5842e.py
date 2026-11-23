#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import yaml
import subprocess
import hashlib
import sqlite3
import datetime
import json
import shlex

def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS backup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            destination TEXT,
            status TEXT,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_backup(db_path: str, source: str, destination: str, status: str, details: str = '') -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('INSERT INTO backup_log (timestamp, source, destination, status, details) VALUES (?,?,?,?,?)',
                (datetime.datetime.utcnow().isoformat(), source, destination, status, details))
    conn.commit()
    conn.close()

def _validate_path(p: str) -> str:
    """
    Basic validation to ensure the path is a string without null bytes.
    """
    if '\x00' in p:
        raise ValueError('Invalid path containing null byte')
    return p

def run_rsync(source: str, destination: str, dry_run: bool = False) -> tuple[bool, str]:
    # Validate inputs to avoid unexpected characters
    src = _validate_path(source.rstrip('/') + '/')
    dst = _validate_path(destination.rstrip('/') + '/')
    cmd = ['rsync', '-a']
    if dry_run:
        cmd.append('--dry-run')
    cmd.extend([src, dst])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            shell=False
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except Exception as e:
        return False, str(e)

def perform_backup(jobs: list[dict], db_path: str, dry_run: bool) -> None:
    for job in jobs:
        src = job.get('source')
        dst = job.get('destination')
        if not src or not dst:
            continue
        if not os.path.isdir(src):
            log_backup(db_path, src, dst, 'failed', 'Source not a directory')
            continue
        success, details = run_rsync(src, dst, dry_run)
        status = 'success' if success else 'failed'
        log_backup(db_path, src, dst, status, details)

def load_state(state_path: str) -> dict:
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state_path: str, state: dict) -> None:
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def main() -> None:
    parser = argparse.ArgumentParser(description='Simple backup utility')
    parser.add_argument('config', help='Path to YAML configuration file')
    parser.add_argument('--db', default='backup_log.db', help='Path to SQLite DB file')
    parser.add_argument('--state', default='backup_state.json', help='Path to state file')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run')
    args = parser.parse_args()

    config = load_config(args.config)
    jobs = config.get('jobs', [])
    if not jobs:
        print('No backup jobs defined in config')
        sys.exit(1)

    init_db(args.db)
    state = load_state(args.state)
    perform_backup(jobs, args.db, args.dry_run)
    save_state(args.state, state)

if __name__ == '__main__':
    main()