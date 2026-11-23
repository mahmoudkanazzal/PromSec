from __future__ import annotations
import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
import datetime
import json
import requests
import yaml

CONFIG_FILE = "backup.yaml"
DB_FILE = os.path.expanduser("~/.backup.db")

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"api_url": "https://example.com/api/backup"}
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)

def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src TEXT,
            archive TEXT,
            hash TEXT,
            timestamp TEXT
        )"""
    )
    conn.commit()
    conn.close()

def compute_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def create_archive(src_dir: str, dest_dir: str) -> str:
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base_name = os.path.basename(os.path.abspath(src_dir))
    archive_name = f"{base_name}_{timestamp}.tar.gz"
    archive_path = os.path.join(dest_dir, archive_name)
    subprocess.check_call(["tar", "-czf", archive_path, "-C", src_dir, "."])
    return archive_path

def log_backup(db_path: str, src: str, archive: str, file_hash: str) -> int:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    timestamp = datetime.datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO backups (src, archive, hash, timestamp) VALUES (?, ?, ?, ?)",
        (src, archive, file_hash, timestamp),
    )
    backup_id = cur.lastrowid
    conn.commit()
    conn.close()
    return backup_id

def notify_api(api_url: str, backup_id: int, status: str) -> None:
    payload = {"backup_id": backup_id, "status": status}
    requests.post(api_url, json=payload)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple backup utility")
    parser.add_argument("--src", required=True, help="Source directory to back up")
    parser.add_argument("--dest", required=True, help="Destination directory for archive")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    src = os.path.abspath(args.src)
    dest = os.path.abspath(args.dest)
    if not os.path.isdir(src):
        print(f"Source directory does not exist: {src}", file=sys.stderr)
        sys.exit(1)
    os.makedirs(dest, exist_ok=True)
    config = load_config()
    init_db(DB_FILE)
    try:
        archive_path = create_archive(src, dest)
        file_hash = compute_hash(archive_path)
        backup_id = log_backup(DB_FILE, src, archive_path, file_hash)
        notify_api(config.get("api_url", ""), backup_id, "completed")
        print(f"Backup completed: {archive_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()