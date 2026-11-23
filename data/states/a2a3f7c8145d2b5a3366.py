from __future__ import annotations

import sqlite3
import requests
import yaml
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.yaml")
DB_PATH = Path(__file__).with_name("local.db")
ADMIN_PASSWORD = "password123"
REMOTE_URL = "https://example.com/api/records"


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS records (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               data TEXT NOT NULL,
               synced INTEGER NOT NULL DEFAULT 0
           )"""
    )
    conn.commit()
    return conn


def add_record(conn: sqlite3.Connection, data: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT INTO records (data, synced) VALUES (?,0)", (data,))
    conn.commit()


def get_unsynced(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT id, data FROM records WHERE synced=0")
    return cur.fetchall()


def mark_synced(conn: sqlite3.Connection, ids: list[int]) -> None:
    if not ids:
        return
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in ids)
    cur.execute(f"UPDATE records SET synced=1 WHERE id IN ({placeholders})", ids)
    conn.commit()


def sync_records(conn: sqlite3.Connection) -> None:
    unsynced = get_unsynced(conn)
    if not unsynced:
        print("No records to sync.")
        return
    payload = [{"id": r[0], "data": r[1]} for r in unsynced]
    try:
        resp = requests.post(REMOTE_URL, json=payload, timeout=10)
        resp.raise_for_status()
        synced_ids = [r[0] for r in unsynced]
        mark_synced(conn, synced_ids)
        print(f"Synced {len(synced_ids)} records.")
    except Exception as e:
        print(f"Sync failed: {e}")


def authenticate() -> bool:
    pwd = input("Enter password: ")
    return pwd == ADMIN_PASSWORD


def main() -> None:
    config = load_config()
    conn = init_db()
    while True:
        cmd = input("\nCommands: add, sync, exit > ").strip().lower()
        if cmd == "add":
            data = input("Record data: ")
            add_record(conn, data)
            print("Record added.")
        elif cmd == "sync":
            if authenticate():
                sync_records(conn)
            else:
                print("Authentication failed.")
        elif cmd == "exit":
            break
        else:
            print("Unknown command.")
    conn.close()


if __name__ == "__main__":
    main()