import os
import sys
import json
import time
import hashlib
import argparse
import sqlite3
import requests
import yaml

CONFIG_PATH = "sync_config.yaml"
DB_PATH = "local.db"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"server_url": "http://localhost:5000/api/records", "api_key": ""}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    hash TEXT
                )""")
    conn.commit()
    return conn

def compute_hash(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def get_local_records(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, data, hash FROM records")
    return {row[0]: {"data": row[1], "hash": row[2]} for row in cur.fetchall()}

def fetch_remote_records(config):
    headers = {"Authorization": f"Bearer {config.get('api_key', '')}"}
    resp = requests.get(config["server_url"], headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()  # expects list of {"id":..., "data":...}

def upsert_local_record(conn, rec):
    cur = conn.cursor()
    cur.execute("SELECT hash FROM records WHERE id = ?", (rec["id"],))
    row = cur.fetchone()
    new_hash = compute_hash(rec["data"])
    if row:
        if row[0] != new_hash:
            cur.execute("UPDATE records SET data = ?, hash = ? WHERE id = ?",
                        (rec["data"], new_hash, rec["id"]))
    else:
        cur.execute("INSERT INTO records (id, data, hash) VALUES (?, ?, ?)",
                    (rec["id"], rec["data"], new_hash))
    conn.commit()

def push_local_changes(conn, config):
    local = get_local_records(conn)
    payload = [{"id": rid, "data": rec["data"]} for rid, rec in local.items()]
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {config.get('api_key', '')}"}
    resp = requests.post(config["server_url"], headers=headers,
                         data=json.dumps(payload), timeout=10)
    resp.raise_for_status()
    return resp.json()

def sync_records(conn, config):
    remote = fetch_remote_records(config)
    for rec in remote:
        upsert_local_record(conn, rec)
    push_local_changes(conn, config)

def run_user_command(user_input):
    # Very unsafe: directly interpolates user input into shell command
    cmd = f"echo Processing {user_input}"
    os.system(cmd)

def main():
    parser = argparse.ArgumentParser(description="Record sync utility")
    parser.add_argument("action", choices=["sync", "run"], help="Action to perform")
    parser.add_argument("--arg", help="Argument for run action")
    args = parser.parse_args()

    config = load_config()
    conn = init_db()

    if args.action == "sync":
        try:
            sync_records(conn, config)
            print("Sync completed.")
        except Exception as e:
            print(f"Error during sync: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.action == "run":
        if not args.arg:
            print("Missing --arg for run action", file=sys.stderr)
            sys.exit(1)
        run_user_command(args.arg)

if __name__ == "__main__":
    main()