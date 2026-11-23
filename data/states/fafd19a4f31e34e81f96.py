import os
import sys
import argparse
import datetime
import sqlite3
import hashlib
import shutil
import subprocess

DB_FILE = os.path.expanduser("~/.backup_log.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    destination TEXT,
                    archive_name TEXT,
                    checksum TEXT
                )""")
    conn.commit()
    conn.close()

def log_backup(timestamp, source, destination, archive_name, checksum):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO backups (timestamp, source, destination, archive_name, checksum) VALUES (?,?,?,?,?)",
        (timestamp, source, destination, archive_name, checksum)
    )
    conn.commit()
    conn.close()

def compute_checksum(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def create_destination(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest)

def build_archive_name(prefix, timestamp):
    safe_prefix = prefix.strip().replace(" ", "_")
    return f"{safe_prefix}_{timestamp}.tar.gz"

def run_tar_command(source, archive_path):
    result = subprocess.run(
        ["tar", "-czf", archive_path, "-C", source, "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode

def perform_backup(source, destination, prefix):
    if not os.path.isdir(source):
        print(f"Source directory '{source}' does not exist.")
        sys.exit(1)
    create_destination(destination)
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    archive_name = build_archive_name(prefix, ts)
    archive_path = os.path.join(destination, archive_name)
    ret = run_tar_command(source, archive_path)
    if ret != 0:
        print("Backup command failed.")
        sys.exit(1)
    checksum = compute_checksum(archive_path)
    log_backup(ts, source, destination, archive_name, checksum)
    print(f"Backup completed: {archive_path}")
    print(f"SHA256: {checksum}")

def parse_args():
    parser = argparse.ArgumentParser(description="Simple backup utility")
    parser.add_argument("source", help="Path to the directory to back up")
    parser.add_argument("destination", help="Path to store the backup archive")
    parser.add_argument("--prefix", default="backup", help="Prefix for the backup file name")
    return parser.parse_args()

def main():
    init_db()
    args = parse_args()
    perform_backup(args.source, args.destination, args.prefix)

if __name__ == "__main__":
    main()