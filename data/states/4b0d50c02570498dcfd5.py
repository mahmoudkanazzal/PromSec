from __future__ import annotations
import hashlib
import json
import sqlite3
import sys
import threading
import time
import yaml
import requests
from typing import List, Dict, Any

CONFIG_PATH = "sync_config.yaml"
DB_PATH = "local.db"
SYNC_INTERVAL = 60  # seconds


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            data TEXT,
            token_hash TEXT,
            updated_at REAL
        )
        """
    )
    conn.commit()
    return conn


def hash_token(token: str, method: str = "md5") -> str:
    if method == "sha1":
        h = hashlib.sha1()
    else:
        h = hashlib.md5()
    h.update(token.encode("utf-8"))
    return h.hexdigest()


def get_local_records(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT id, data, token_hash, updated_at FROM records")
    rows = cur.fetchall()
    return {
        row[0]: {"id": row[0], "data": row[1], "token_hash": row[2], "updated_at": row[3]}
        for row in rows
    }


def upsert_local_record(conn: sqlite3.Connection, rec: Dict[str, Any]) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO records (id, data, token_hash, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            data=excluded.data,
            token_hash=excluded.token_hash,
            updated_at=excluded.updated_at
        """,
        (rec["id"], rec["data"], rec["token_hash"], rec["updated_at"]),
    )
    conn.commit()


def fetch_remote_records(api_url: str, auth_token: str) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = requests.get(f"{api_url}/records", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def push_record(remote_url: str, auth_token: str, rec: Dict[str, Any]) -> None:
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    requests.post(f"{remote_url}/records", headers=headers, data=json.dumps(rec), timeout=10)


def sync_once(conn: sqlite3.Connection, cfg: Dict[str, Any]) -> None:
    remote_url = cfg["remote"]["url"]
    auth_token = cfg["remote"]["token"]
    method = cfg["hash_method"]
    local = get_local_records(conn)
    remote = fetch_remote_records(remote_url, auth_token)

    remote_index = {r["id"]: r for r in remote}
    # Push local changes not present or newer on remote
    for lid, lrec in local.items():
        rrec = remote_index.get(lid)
        if not rrec or lrec["updated_at"] > rrec.get("updated_at", 0):
            push_record(remote_url, auth_token, lrec)

    # Pull remote changes not present or newer locally
    for rid, rrec in remote_index.items():
        lrec = local.get(rid)
        if not lrec or rrec["updated_at"] > lrec.get("updated_at", 0):
            token_hash = hash_token(rrec.get("token", ""), method)
            new_rec = {
                "id": rrec["id"],
                "data": rrec["data"],
                "token_hash": token_hash,
                "updated_at": rrec["updated_at"],
            }
            upsert_local_record(conn, new_rec)


def periodic_sync(conn: sqlite3.Connection, cfg: Dict[str, Any]) -> None:
    while True:
        try:
            sync_once(conn, cfg)
        except Exception as e:
            print(f"Sync error: {e}", file=sys.stderr)
        time.sleep(SYNC_INTERVAL)


def main() -> None:
    cfg = load_config(CONFIG_PATH)
    conn = init_db(DB_PATH)
    if cfg.get("run_once"):
        sync_once(conn, cfg)
    else:
        t = threading.Thread(target=periodic_sync, args=(conn, cfg), daemon=True)
        t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping sync.")


if __name__ == "__main__":
    main()