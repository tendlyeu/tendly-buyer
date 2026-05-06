"""
Initialize the LOCAL Postgres database for development.

Creates:
  1. The 'tendly' schema and all TendlyBase tables (procurement_plans, chat_contexts, ...)
  2. The 'public' schema Tender* tables that are normally read-only on prod
     (so chat search queries can be exercised locally)
  3. A seed buyer user in tendly.users
  4. A handful of fake tenders so the chat / dashboard have something to render

Usage:
    source venv/bin/activate
    python scripts/init_local_db.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import text

from core.database import (
    _get_engine, _get_tendly_engine,
    Base, TendlyBase,
    TendlyUser, get_tendly_session,
    Tender, TenderDetail, TenderResult, TenderQualityScore,
    get_session,
)


def main():
    print("=== Tendly Buyer — Local DB Initialization ===\n")

    # --------------------------------------------------------------
    # 1. Public-schema (read-only-on-prod) tables — created locally so
    #    chat search has something to query.
    # --------------------------------------------------------------
    print("[1/4] Creating public-schema tables (Tender, TenderDetail, ...)")
    public_engine = _get_engine()
    Base.metadata.create_all(bind=public_engine)
    for t in sorted(Base.metadata.tables.keys()):
        print(f"      - {t}")
    print(f"      {len(Base.metadata.tables)} tables ensured.\n")

    # --------------------------------------------------------------
    # 2. tendly schema + tables
    # --------------------------------------------------------------
    print("[2/4] Creating 'tendly' schema and TendlyBase tables")
    tendly_engine = _get_tendly_engine()
    with tendly_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS tendly"))
        conn.commit()
    TendlyBase.metadata.create_all(bind=tendly_engine)
    for t in sorted(TendlyBase.metadata.tables.keys()):
        print(f"      - {t}")
    print(f"      {len(TendlyBase.metadata.tables)} tables ensured.\n")

    # --------------------------------------------------------------
    # 3. Seed buyer user
    # --------------------------------------------------------------
    print("[3/4] Seeding test buyer user")
    test_email = "buyer@tendly.local"
    test_password = "buyer123"
    test_name = "Local Buyer"

    sess = get_tendly_session()
    try:
        existing = sess.query(TendlyUser).filter(TendlyUser.email == test_email).first()
        if existing:
            print(f"      User '{test_email}' already exists (id={existing.id}). Skipping.\n")
        else:
            password_hash = bcrypt.hashpw(
                test_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            user = TendlyUser(
                email=test_email,
                password_hash=password_hash,
                name=test_name,
                role="buyer",
                company="Tendly Local Test Org",
                country="EE",
                language="en",
                is_active=True,
            )
            sess.add(user)
            sess.commit()
            print(f"      Created user '{test_email}' (password: '{test_password}', role='buyer').\n")
    finally:
        sess.close()

    # --------------------------------------------------------------
    # 4. Seed sample tenders so the chat & registry have data
    # --------------------------------------------------------------
    print("[4/4] Seeding sample tenders")
    sess = get_session()
    try:
        sample = [
            {
                "procurement_id": 1001,
                "procurement_reference_nr": "EE-2026-001",
                "procurement_name": "IT-süsteemi hooldus",
                "procurement_name_en": "IT system maintenance",
                "procurement_name_et": "IT-süsteemi hooldus",
                "contracting_authority_name": "Tallinna Linnavalitsus",
                "procurement_status": "active",
                "procurement_type": "T",
                "main_cpv_id": 72000000,
                "main_cpv_name": "IT services",
                "country": "Estonia",
                "country_code": "EE",
                "currency": "EUR",
                "estimated_cost": 150000.0,
                "deadline_days": 30,
            },
            {
                "procurement_id": 1002,
                "procurement_reference_nr": "EE-2026-002",
                "procurement_name": "Tee remont – Tartu",
                "procurement_name_en": "Road repair — Tartu",
                "procurement_name_et": "Tee remont – Tartu",
                "contracting_authority_name": "Tartu Linnavalitsus",
                "procurement_status": "active",
                "procurement_type": "E",
                "main_cpv_id": 45233000,
                "main_cpv_name": "Construction works for highways, roads",
                "country": "Estonia",
                "country_code": "EE",
                "currency": "EUR",
                "estimated_cost": 850000.0,
                "deadline_days": 45,
            },
            {
                "procurement_id": 1003,
                "procurement_reference_nr": "GB-2026-001",
                "procurement_name": "School supplies framework",
                "procurement_name_en": "School supplies framework",
                "contracting_authority_name": "Manchester City Council",
                "procurement_status": "active",
                "procurement_type": "A",
                "main_cpv_id": 30192000,
                "main_cpv_name": "Office supplies",
                "country": "United Kingdom",
                "country_code": "GB",
                "currency": "GBP",
                "estimated_cost": 220000.0,
                "deadline_days": 60,
            },
        ]

        now = datetime.utcnow()
        for s in sample:
            existing = sess.query(Tender).filter(
                Tender.procurement_id == s["procurement_id"]
            ).first()
            if existing:
                continue

            t = Tender(
                procurement_id=s["procurement_id"],
                procurement_reference_nr=s["procurement_reference_nr"],
                procurement_name=s["procurement_name"],
                procurement_name_en=s.get("procurement_name_en", ""),
                procurement_name_et=s.get("procurement_name_et", ""),
                contracting_authority_name=s["contracting_authority_name"],
                procurement_status=s["procurement_status"],
                procurement_type=s["procurement_type"],
                main_cpv_id=s["main_cpv_id"],
                main_cpv_name=s["main_cpv_name"],
                country=s["country"],
                country_code=s["country_code"],
                currency=s["currency"],
            )
            d = TenderDetail(
                procurement_id=s["procurement_id"],
                estimated_cost=s["estimated_cost"],
                submission_deadline=now + timedelta(days=s["deadline_days"]),
                tender_name=s["procurement_name"],
                tender_name_en=s.get("procurement_name_en", ""),
                tender_name_et=s.get("procurement_name_et", ""),
                primary_cpv_id=s["main_cpv_id"],
                primary_cpv_name=s["main_cpv_name"],
            )
            sess.add(t)
            sess.add(d)

        sess.commit()
        count = sess.query(Tender).count()
        print(f"      {count} total tenders in DB.\n")
    finally:
        sess.close()

    print("=== Done ===")
    print(f"\nLogin credentials: {test_email} / {test_password}")


if __name__ == "__main__":
    main()
