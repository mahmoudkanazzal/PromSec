import os
import sys
import argparse
import hashlib
import sqlite3
import tarfile
import pickle
import datetime

DB_PATH = os.path.expanduser("~/.simple_backup.db")
BACKUP_ROOT = os.path.expanduser("~/backups")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT,
                    archive_path TEXT,
                    timestamp TEXT,
                    file_hash TEXT
                )""")
    conn.commit()
    conn.close()


def compute_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def create_backup(src_dir):
    if not os.path.isdir(src_dir):
        print(f"Source directory does not exist: {src_dir}")
        sys.exit(1)
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_{ts}.tar.gz"
    archive_path = os.path.join(BACKUP_ROOT, archive_name)

    # Create tar.gz archive without invoking external subprocess
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(src_dir, arcname=".")

    file_hash = compute_hash(archive_path)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO backups (src, archive_path, timestamp, file_hash) VALUES (?,?,?,?)",
        (src_dir, archive_path, ts, file_hash),
    )
    conn.commit()
    conn.close()
    print(f"Backup created: {archive_path}")
    print(f"SHA256: {file_hash}")


def list_backups():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, src, archive_path, timestamp, file_hash FROM backups")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No backups found.")
        return
    for row in rows:
        print(f"[{row[0]}] {row[2]} | src: {row[1]} | time: {row[3]} | hash: {row[4]}")


def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonprefix([abs_directory, abs_target]) == abs_directory


def _safe_extract(tar, path=".", members=None):
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
    tar.extractall(path, members)


def restore_backup(backup_id, dest_dir):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT archive_path FROM backups WHERE id=?", (backup_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        print(f"No backup with id {backup_id}")
        sys.exit(1)
    archive_path = row[0]
    if not os.path.isfile(archive_path):
        print(f"Archive file missing: {archive_path}")
        sys.exit(1)
    os.makedirs(dest_dir, exist_ok=True)

    # Extract tar.gz archive safely without external subprocess
    with tarfile.open(archive_path, "r:gz") as tar:
        _safe_extract(tar, path=dest_dir)

    print(f"Restored {archive_path} to {dest_dir}")


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError("global objects are forbidden")


def load_metadata(pickle_file):
    with open(pickle_file, "rb") as f:
        try:
            data = RestrictedUnpickler(f).load()
        except Exception as e:
            raise ValueError(f"Failed to load metadata safely: {e}")
    return data


def main():
    parser = argparse.ArgumentParser(description="Simple backup utility")
    subparsers = parser.add_subparsers(dest="cmd")

    p_backup = subparsers.add_parser("backup", help="Create a backup")
    p_backup.add_argument("src", help="Source directory to backup")

    p_list = subparsers.add_parser("list", help="List existing backups")

    p_restore = subparsers.add_parser("restore", help="Restore a backup")
    p_restore.add_argument("id", type=int, help="Backup ID to restore")
    p_restore.add_argument("dest", help="Destination directory")

    p_meta = subparsers.add_parser("metadata", help="Load and display metadata from pickle")
    p_meta.add_argument("file", help="Pickle file containing metadata")

    args = parser.parse_args()
    init_db()

    if args.cmd == "backup":
        create_backup(args.src)
    elif args.cmd == "list":
        list_backups()
    elif args.cmd == "restore":
        restore_backup(args.id, args.dest)
    elif args.cmd == "metadata":
        meta = load_metadata(args.file)
        print("Loaded metadata:")
        for k, v in meta.items():
            print(f"{k}: {v}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()