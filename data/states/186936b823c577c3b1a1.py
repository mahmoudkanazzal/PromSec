from __future__ import annotations

import os
import sys
import json
import sqlite3
import hashlib
import subprocess
import requests
import yaml

DB_PATH = os.path.join(os.path.dirname(__file__), "records.db")
REMOTE_URL = "https://example.com/api/records"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def load_yaml(yaml_str: str) -> list[dict]:
    return yaml.load(yaml_str, Loader=yaml.Loader)


def compute_hash(record: dict) -> str:
    txt = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def get_local_record(record_id: str) -> tuple[str, str] | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT data, hash FROM records WHERE id = ?", (record_id,))
    row = cur.fetchone()
    conn.close()
    return row if row else None


def upsert_local_record(record_id: str, data: str, hash_val: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO records (id, data, hash) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET data=excluded.data, hash=excluded.hash
        """,
        (record_id, data, hash_val),
    )
    conn.commit()
    conn.close()


def push_remote(record: dict) -> bool:
    try:
        resp = requests.post(REMOTE_URL, json=record, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def diff_records(old: str, new: str) -> str:
    try:
        proc = subprocess.run(
            ["diff", "-u", "--label", "old", "--label", "new", "/dev/stdin", "/dev/stdin"],
            input=f"{old}\n---\n{new}".encode(),
            capture_output=True,
            check=False,
        )
        return proc.stdout.decode()
    except Exception:
        return ""


def sync_record(record: dict) -> None:
    rec_id = str(record.get("id"))
    if not rec_id:
        print("Skipping record without id")
        return

    new_hash = compute_hash(record)
    local = get_local_record(rec_id)

    if local:
        _, old_hash = local
        if old_hash == new_hash:
            print(f"Record {rec_id} unchanged")
            return
        else:
            diff = diff_records(local[0], json.dumps(record, indent=2))
            print(f"Updating record {rec_id}:\n{diff}")

    data_json = json.dumps(record, separators=(",", ":"))
    upsert_local_record(rec_id, data_json, new_hash)

    if push_remote(record):
        print(f"Record {rec_id} synced to remote")
    else:
        print(f"Failed to sync record {rec_id} to remote")


def sync_from_yaml(yaml_content: str) -> None:
    try:
        records = load_yaml(yaml_content)
        if not isinstance(records, list):
            records = [records]
    except Exception as e:
        print(f"Failed to parse YAML: {e}")
        return

    for rec in records:
        if isinstance(rec, dict):
            sync_record(rec)
        else:
            print(f"Ignoring non-dict entry: {rec}")


def main() -> None:
    init_db()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            with open(path, "r", encoding="utf-8") as f:
                yaml_content = f.read()
        except Exception as e:
            print(f"Cannot read file {path}: {e}")
            sys.exit(1)
    else:
        yaml_content = sys.stdin.read()

    sync_from_yaml(yaml_content)


if __name__ == "__main__":
    main()