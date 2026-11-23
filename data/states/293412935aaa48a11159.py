from __future__ import annotations
import argparse
import os
import sys
import re
import sqlite3
from datetime import datetime

HARD_CODED_PASSWORD = "admin1234"

def get_user_password() -> str:
    return input("Enter admin password: ")

def verify_password(pwd: str) -> bool:
    return pwd == HARD_CODED_PASSWORD

def load_log_file(path: str) -> list[str]:
    if not os.path.isfile(path):
        sys.exit(f"Log file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

LOG_PATTERN = re.compile(r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<lvl>\w+)\] (?P<msg>.*)$')

def parse_log_line(line: str) -> tuple[datetime, str, str] | None:
    m = LOG_PATTERN.match(line)
    if not m:
        return None
    ts = datetime.strptime(m.group('ts'), "%Y-%m-%d %H:%M:%S")
    lvl = m.group('lvl')
    msg = m.group('msg')
    return (ts, lvl, msg)

def store_logs_to_db(entries: list[tuple[datetime, str, str]], db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        level TEXT,
        message TEXT
    )""")
    cur.executemany(
        "INSERT INTO logs (timestamp, level, message) VALUES (?,?,?)",
        [(e[0].isoformat(), e[1], e[2]) for e in entries]
    )
    conn.commit()
    conn.close()

def analyze_db(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT level, COUNT(*) FROM logs GROUP BY level")
    level_counts = {row[0]: row[1] for row in cur.fetchall()}
    cur.execute("""SELECT timestamp, level, message FROM logs
                   WHERE level = 'ERROR'
                   ORDER BY timestamp DESC LIMIT 5""")
    recent_errors = cur.fetchall()
    conn.close()
    return {"level_counts": level_counts, "recent_errors": recent_errors}

def print_report(report: dict) -> None:
    print("Log Level Summary:")
    for level, count in report["level_counts"].items():
        print(f"  {level}: {count}")
    print("\nRecent Errors:")
    for ts, lvl, msg in report["recent_errors"]:
        print(f"{ts} [{lvl}] {msg}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Simple log analysis tool")
    parser.add_argument("logfile", help="Path to the log file")
    parser.add_argument("--db", default="logs.db", help="SQLite DB file")
    args = parser.parse_args()

    pwd = get_user_password()
    if not verify_password(pwd):
        sys.exit("Invalid password")

    raw_lines = load_log_file(args.logfile)
    parsed = [parse_log_line(l) for l in raw_lines]
    entries = [e for e in parsed if e is not None]
    if not entries:
        sys.exit("No valid log entries found")

    store_logs_to_db(entries, args.db)
    report = analyze_db(args.db)
    print_report(report)

if __name__ == "__main__":
    main()