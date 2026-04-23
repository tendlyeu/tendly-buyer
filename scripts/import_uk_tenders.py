"""
Import UK tender data from the Contracts Finder OCDS API.

Downloads tenders and awards from:
https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search

Usage: python scripts/import_uk_tenders.py [--limit 500]
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

import requests
import psycopg2
from psycopg2.extras import Json

DB_URL = os.environ.get(
    "TENDLY_DB_URL",
    "postgresql://finespresso:mlfpass2026@72.62.114.124:5432/finespresso_db",
)

OCDS_URL = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"


def fetch_releases(max_releases=500):
    """Fetch OCDS releases from Contracts Finder with cursor pagination."""
    all_releases = []
    url = OCDS_URL
    params = {
        "limit": 100,
        "stages": "tender,award",
        "publishedFrom": "2025-01-01T00:00:00Z",
    }
    page = 0

    while url and len(all_releases) < max_releases:
        page += 1
        print(f"  Fetching page {page} (have {len(all_releases)} releases)...")

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

        releases = data.get("releases", [])
        if not releases:
            break

        all_releases.extend(releases)

        # Follow cursor pagination
        next_url = data.get("links", {}).get("next")
        if next_url:
            url = next_url
            params = {}  # cursor URL has all params
        else:
            break

        time.sleep(0.5)  # be polite

    return all_releases[:max_releases]


def parse_release(release):
    """Parse an OCDS release into tender + award dicts."""
    tender_data = release.get("tender", {})
    buyer = release.get("buyer", {})
    classification = tender_data.get("classification", {})
    value = tender_data.get("value", {})
    tender_period = tender_data.get("tenderPeriod", {})
    contract_period = tender_data.get("contractPeriod", {})
    suitability = tender_data.get("suitability", {})

    # Find notice URL from documents
    notice_url = ""
    for doc in tender_data.get("documents", []):
        if doc.get("url"):
            notice_url = doc["url"]
            break

    tender = {
        "external_id": release.get("ocid", ""),
        "source": "contracts_finder",
        "title": tender_data.get("title", "Untitled"),
        "description": tender_data.get("description", ""),
        "status": tender_data.get("status", "active"),
        "procurement_method": tender_data.get("procurementMethod", ""),
        "procurement_method_details": tender_data.get("procurementMethodDetails", ""),
        "main_category": tender_data.get("mainProcurementCategory", ""),
        "cpv_code": classification.get("id", ""),
        "cpv_description": classification.get("description", ""),
        "estimated_value": value.get("amount"),
        "currency": value.get("currency", "GBP"),
        "buyer_name": buyer.get("name", ""),
        "buyer_id": buyer.get("id", ""),
        "submission_deadline": _parse_date(tender_period.get("endDate")),
        "contract_start": _parse_date(contract_period.get("startDate")),
        "contract_end": _parse_date(contract_period.get("endDate")),
        "country_code": "GB",
        "notice_url": notice_url,
        "is_sme_suitable": suitability.get("sme", False) if isinstance(suitability, dict) else False,
        "published_date": _parse_date(release.get("date")),
        "raw_data": release,
    }

    # Parse awards
    awards = []
    for award in release.get("awards", []):
        for supplier in award.get("suppliers", []):
            awards.append({
                "supplier_name": supplier.get("name", ""),
                "supplier_id": supplier.get("id", ""),
                "award_value": award.get("value", {}).get("amount"),
                "currency": award.get("value", {}).get("currency", "GBP"),
                "award_date": _parse_date(award.get("date")),
                "status": award.get("status", ""),
            })

    return tender, awards


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        # Handle various ISO formats
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def insert_data(releases):
    """Insert parsed releases into tendly.tenders and tendly.awards."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    inserted_tenders = 0
    inserted_awards = 0
    skipped = 0

    for release in releases:
        tender, awards = parse_release(release)

        # Skip if no title
        if not tender["title"] or tender["title"] == "Untitled":
            skipped += 1
            continue

        # Check for duplicate by external_id
        cur.execute(
            "SELECT id FROM tendly.tenders WHERE external_id = %s",
            (tender["external_id"],),
        )
        existing = cur.fetchone()
        if existing:
            tender_id = existing[0]
            skipped += 1
        else:
            cur.execute("""
                INSERT INTO tendly.tenders (
                    external_id, source, title, description, status,
                    procurement_method, procurement_method_details,
                    main_category, cpv_code, cpv_description,
                    estimated_value, currency, buyer_name, buyer_id,
                    submission_deadline, contract_start, contract_end,
                    country_code, notice_url, is_sme_suitable,
                    published_date, raw_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                tender["external_id"], tender["source"],
                tender["title"], tender["description"], tender["status"],
                tender["procurement_method"], tender["procurement_method_details"],
                tender["main_category"], tender["cpv_code"], tender["cpv_description"],
                tender["estimated_value"], tender["currency"],
                tender["buyer_name"], tender["buyer_id"],
                tender["submission_deadline"], tender["contract_start"], tender["contract_end"],
                tender["country_code"], tender["notice_url"], tender["is_sme_suitable"],
                tender["published_date"], Json(tender["raw_data"]),
            ))
            tender_id = cur.fetchone()[0]
            inserted_tenders += 1

        # Insert awards
        for award in awards:
            cur.execute("""
                INSERT INTO tendly.awards (
                    tender_id, supplier_name, supplier_id,
                    award_value, currency, award_date, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                tender_id, award["supplier_name"], award["supplier_id"],
                award["award_value"], award["currency"],
                award["award_date"], award["status"],
            ))
            inserted_awards += 1

    conn.commit()
    cur.close()
    conn.close()

    return inserted_tenders, inserted_awards, skipped


def main():
    parser = argparse.ArgumentParser(description="Import UK tenders from Contracts Finder")
    parser.add_argument("--limit", type=int, default=500, help="Max releases to fetch")
    args = parser.parse_args()

    print(f"Fetching up to {args.limit} UK tender releases...")
    releases = fetch_releases(args.limit)
    print(f"Fetched {len(releases)} releases.\n")

    if not releases:
        print("No releases to import.")
        return

    print("Inserting into tendly schema...")
    tenders, awards, skipped = insert_data(releases)
    print(f"\nDone!")
    print(f"  Tenders inserted: {tenders}")
    print(f"  Awards inserted:  {awards}")
    print(f"  Skipped (dupes):  {skipped}")


if __name__ == "__main__":
    main()
