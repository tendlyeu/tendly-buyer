"""
Initialize the tendly schema and seed a test user.

Usage (run manually by Kamel):
    cd tendly-buyer
    source venv/bin/activate
    python scripts/init_db.py

This script:
  1. Connects to TENDLY_DB_URL
  2. Creates the 'tendly' schema if it does not exist
  3. Creates all tables defined in TendlyBase.metadata
  4. Seeds a test buyer user (kamelbelkadhi2+kkkkkkk@gmail.com / admin212)

Requires: bcrypt, sqlalchemy, psycopg2-binary (all in requirements.txt)
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import bcrypt
from sqlalchemy import text
from core.database import _get_tendly_engine, TendlyBase, TendlyUser, get_tendly_session


def main():
    print("=== Tendly Buyer — Database Initialization ===\n")

    engine = _get_tendly_engine()
    url = str(engine.url)
    # Mask password in output
    masked = url
    if "@" in masked:
        pre, post = masked.split("@", 1)
        if ":" in pre:
            driver_user = pre.rsplit(":", 1)[0]
            masked = f"{driver_user}:****@{post}"
    print(f"Target database: {masked}\n")

    # Step 1: Create schema
    print("[1/3] Creating 'tendly' schema if not exists...")
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS tendly"))
        conn.commit()
    print("      Done.\n")

    # Step 2: Create all tables from TendlyBase metadata
    print("[2/3] Creating tables from TendlyBase.metadata...")
    TendlyBase.metadata.create_all(bind=engine)
    table_names = sorted(TendlyBase.metadata.tables.keys())
    for t in table_names:
        print(f"      - {t}")
    print(f"      {len(table_names)} table(s) ensured.\n")

    # Step 3: Seed test user
    print("[3/3] Seeding test buyer user...")
    test_email = "kamelbelkadhi2+kkkkkkk@gmail.com"
    test_password = "admin212"
    test_name = "Kamel (Test Buyer)"

    session = get_tendly_session()
    try:
        existing = (
            session.query(TendlyUser)
            .filter(TendlyUser.email == test_email)
            .first()
        )
        if existing:
            print(f"      User '{test_email}' already exists (id={existing.id}). Skipping.")
        else:
            password_hash = bcrypt.hashpw(
                test_password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

            user = TendlyUser(
                email=test_email,
                password_hash=password_hash,
                name=test_name,
                role="buyer",
                company="Tendly Test Org",
                country="EE",
                language="en",
                is_active=True,
            )
            session.add(user)
            session.commit()
            print(f"      Created user '{test_email}' with role='buyer'.")
    except Exception as e:
        session.rollback()
        print(f"      Error seeding user: {e}")
        raise
    finally:
        session.close()

    print("\n=== Initialization complete ===")


if __name__ == "__main__":
    main()
