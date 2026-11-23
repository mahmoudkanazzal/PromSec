from __future__ import annotations
import argparse
import hashlib
import os
import sqlite3
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from flask import Flask, jsonify, send_file, abort

DB_FILE = "backups.db"
BACKUP_DIR = Path("backup_store")
APP = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS backups (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               timestamp TEXT,
               archive_path TEXT,
               size INTEGER,
               sha256 TEXT
           )"""
    )
    conn.commit()
    conn.close()

def add_backup_record(timestamp: str, archive_path: str, size: int, sha256: str) -> int:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO backups (timestamp, archive_path, size, sha256) VALUES (?,?,?,?)",
        (timestamp, archive_path, size, sha256),
    )
    backup_id = cur.lastrowid
    conn.commit()
    conn.close()
    return backup_id

def list_backups() -> List[Tuple[int, str, str, int, str]]:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, archive_path, size, sha256 FROM backups ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_backup(backup_id: int) -> Tuple[int, str, str, int, str] | None:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, archive_path, size, sha256 FROM backups WHERE id = ?", (backup_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def create_backup(source_path: Path) -> None:
    if not source_path.is_dir():
        print(f"Error: {source_path} is not a directory")
        sys.exit(1)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    archive_name = f"{timestamp}.tar.gz"
    archive_path = BACKUP_DIR / archive_name
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(source_path, arcname=source_path.name)
    size = archive_path.stat().st_size
    sha = compute_sha256(archive_path)
    backup_id = add_backup_record(timestamp, str(archive_path), size, sha)
    print(f"Backup created: ID={backup_id}, file={archive_path}")

def _is_within_directory(directory: Path, target: Path) -> bool:
    try:
        directory = directory.resolve()
        target = target.resolve()
        return str(target).startswith(str(directory) + os.sep)
    except Exception:
        return False

def _safe_extract(tar: tarfile.TarFile, path: Path) -> None:
    for member in tar.getmembers():
        member_path = path / member.name
        if not _is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
    tar.extractall(path)

def restore_backup(backup_id: int, target_dir: Path) -> None:
    record = get_backup(backup_id)
    if not record:
        print(f"No backup found with ID {backup_id}")
        sys.exit(1)
    archive_path = Path(record[2])
    if not archive_path.is_file():
        print(f"Archive file missing: {archive_path}")
        sys.exit(1)
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        _safe_extract(tar, target_dir)
    print(f"Restored backup {backup_id} to {target_dir}")

@APP.route("/backups", methods=["GET"])
def api_list_backups():
    rows = list_backups()
    data = [
        {
            "id": r[0],
            "timestamp": r[1],
            "archive": r[2],
            "size": r[3],
            "sha256": r[4],
        }
        for r in rows
    ]
    return jsonify(data)

@APP.route("/download/<int:backup_id>", methods=["GET"])
def api_download_backup(backup_id: int):
    record = get_backup(backup_id)
    if not record:
        abort(404)
    archive_path = Path(record[2])
    if not archive_path.is_file():
        abort(404)
    return send_file(str(archive_path), as_attachment=True)

def run_server(host: str = "127.0.0.1", port: int = 5000):
    init_db()
    APP.run(host=host, port=port)

def parse_args():
    parser = argparse.ArgumentParser(description="Simple backup utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bp = subparsers.add_parser("backup", help="Create a backup")
    bp.add_argument("source", type=Path, help="Directory to back up")

    rp = subparsers.add_parser("restore", help="Restore a backup")
    rp.add_argument("id", type=int, help="Backup ID")
    rp.add_argument("target", type=Path, help="Target directory")

    subparsers.add_parser("list", help="List all backups")
    subparsers.add_parser("serve", help="Run HTTP server for backup access")
    return parser.parse_args()

def main():
    args = parse_args()
    init_db()
    if args.command == "backup":
        create_backup(args.source)
    elif args.command == "restore":
        restore_backup(args.id, args.target)
    elif args.command == "list":
        for r in list_backups():
            print(f"ID:{r[0]} Time:{r[1]} Size:{r[3]} SHA256:{r[4]}")
    elif args.command == "serve":
        run_server()
    else:
        print("Unknown command")
        sys.exit(1)

if __name__ == "__main__":
    main()