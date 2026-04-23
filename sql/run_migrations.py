"""
Run SQL migrations against the tendly schema.

Usage: python sql/run_migrations.py
"""

import os
import sys
from pathlib import Path

import psycopg2

DB_URL = os.environ.get(
    "TENDLY_DB_URL",
    "postgresql://finespresso:mlfpass2026@72.62.114.124:5432/finespresso_db",
)

SQL_DIR = Path(__file__).parent


def run():
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    if not sql_files:
        print("No SQL files found.")
        return

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    for f in sql_files:
        print(f"Running {f.name}...")
        sql = f.read_text(encoding="utf-8")
        try:
            cur.execute(sql)
            print(f"  OK")
        except Exception as e:
            print(f"  ERROR: {e}")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
