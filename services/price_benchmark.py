"""Price benchmarking service — queries tendly.tenders and tendly.awards for market prices."""

from typing import Dict, List, Optional
from sqlalchemy import func, or_, desc
from core.database import get_tendly_session, TendlyTender, TendlyAward


def get_price_benchmarks(
    keywords: List[str] = None,
    cpv_divisions: List[str] = None,
    main_category: str = "",
    country_code: str = "GB",
    limit: int = 50,
) -> Dict:
    """Query UK tender data for price benchmarks."""
    db = get_tendly_session()
    try:
        query = db.query(TendlyTender).filter(TendlyTender.estimated_value.isnot(None))

        # Filter by category
        if main_category:
            cat_map = {
                "services": "services", "service": "services",
                "goods": "goods", "supplies": "goods",
                "works": "works", "construction": "works",
            }
            mapped = cat_map.get(main_category.lower(), main_category.lower())
            query = query.filter(TendlyTender.main_category == mapped)

        # Filter by CPV
        if cpv_divisions:
            cpv_filters = [TendlyTender.cpv_code.like(f"{d}%") for d in cpv_divisions]
            query = query.filter(or_(*cpv_filters))

        # Filter by keywords in title/description
        if keywords:
            kw_filters = []
            for kw in keywords:
                if len(kw) > 2:
                    kw_filters.append(TendlyTender.title.ilike(f"%{kw}%"))
                    kw_filters.append(TendlyTender.description.ilike(f"%{kw}%"))
                    kw_filters.append(TendlyTender.cpv_description.ilike(f"%{kw}%"))
            if kw_filters:
                query = query.filter(or_(*kw_filters))

        # Order by most recent
        query = query.order_by(desc(TendlyTender.published_date))
        results = query.limit(limit).all()

        if not results:
            return {"contracts": [], "stats": {}, "awards": []}

        # Compute stats
        values = [float(r.estimated_value) for r in results if r.estimated_value]
        sorted_values = sorted(values)

        stats = {}
        if values:
            stats = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "median": sorted_values[len(sorted_values) // 2],
                "min": min(values),
                "max": max(values),
                "p25": sorted_values[len(sorted_values) // 4] if len(sorted_values) > 3 else min(values),
                "p75": sorted_values[3 * len(sorted_values) // 4] if len(sorted_values) > 3 else max(values),
            }

        # Format contracts
        contracts = []
        tender_ids = []
        for r in results[:30]:
            contracts.append({
                "id": r.id,
                "title": r.title,
                "buyer": r.buyer_name or "",
                "value": float(r.estimated_value) if r.estimated_value else None,
                "currency": r.currency or "GBP",
                "category": r.main_category or "",
                "cpv_code": r.cpv_code or "",
                "cpv_description": r.cpv_description or "",
                "status": r.status or "",
                "deadline": r.submission_deadline.isoformat() if r.submission_deadline else None,
                "notice_url": r.notice_url or "",
                "procurement_method": r.procurement_method_details or r.procurement_method or "",
            })
            tender_ids.append(r.id)

        # Fetch awards for these tenders
        awards_data = []
        if tender_ids:
            awards = (
                db.query(TendlyAward)
                .filter(TendlyAward.tender_id.in_(tender_ids))
                .order_by(desc(TendlyAward.award_value))
                .limit(20)
                .all()
            )
            for a in awards:
                awards_data.append({
                    "tender_id": a.tender_id,
                    "supplier": a.supplier_name or "",
                    "value": float(a.award_value) if a.award_value else None,
                    "currency": a.currency or "GBP",
                    "date": a.award_date.isoformat() if a.award_date else None,
                })

        # Category breakdown
        category_counts = {}
        for r in results:
            cat = r.main_category or "other"
            if cat not in category_counts:
                category_counts[cat] = {"count": 0, "total_value": 0}
            category_counts[cat]["count"] += 1
            if r.estimated_value:
                category_counts[cat]["total_value"] += float(r.estimated_value)

        return {
            "contracts": contracts,
            "stats": stats,
            "awards": awards_data,
            "categories": category_counts,
            "search_params": {
                "keywords": keywords or [],
                "cpv_divisions": cpv_divisions or [],
                "main_category": main_category,
            },
        }

    except Exception as e:
        print(f"Price benchmark error: {e}")
        import traceback
        traceback.print_exc()
        return {"contracts": [], "stats": {}, "awards": []}
    finally:
        db.close()
