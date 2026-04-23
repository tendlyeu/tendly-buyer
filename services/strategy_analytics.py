"""
Competitor Strategy Analytics Service — ported from tendly-main.

Analyzes a company's winning history from public award notices to identify
pricing strategies, sector preferences, buyer relationships, and competition levels.
"""

from sqlalchemy import func, desc, or_
from datetime import datetime
from typing import Dict, List, Optional

from core.database import get_session, Tender, TenderDetail, TenderResult


def get_competitor_strategy_analysis(
    identifier: str,
    country: str = None,
    db=None,
) -> Dict:
    """Comprehensive strategy analysis for a competitor.

    Args:
        identifier: Registry code or company name
        country: Optional country code filter (e.g. EE, GB, LV, PL, LT, FR)
        db: Optional database session
    """
    should_close = False
    if db is None:
        db = get_session()
        should_close = True

    try:
        company_info = _resolve_company(identifier, country, db)
        if not company_info:
            return {"error": "company_not_found", "company": None, "insights": {}}

        company_name = company_info["name"]
        company_reg_code = company_info["reg_code"]

        if company_reg_code:
            company_filter = or_(
                TenderResult.winner_reg_code == company_reg_code,
                TenderResult.winner_name == company_name,
            )
        else:
            company_filter = TenderResult.winner_name == company_name

        # Get all won tenders with full details
        query = (
            db.query(TenderResult, Tender, TenderDetail)
            .join(Tender, TenderResult.procurement_id == Tender.procurement_id)
            .outerjoin(TenderDetail, Tender.procurement_id == TenderDetail.procurement_id)
            .filter(
                company_filter,
                TenderResult.winner_name.isnot(None),
                TenderResult.winner_name != "",
            )
        )
        if country:
            query = query.filter(Tender.country_code == country)

        won_tenders = query.order_by(desc(Tender.created_at)).all()

        if not won_tenders:
            return {
                "error": None,
                "company": company_info,
                "total_wins": 0,
                "total_value": 0,
                "insights": {},
            }

        total_value = sum(
            (r.contract_actual_cost or r.contract_cost or 0)
            for r, t, td in won_tenders
        )

        insights = {
            "pricing_strategy": _analyze_pricing_strategy(won_tenders),
            "buyer_relationships": _analyze_buyer_relationships(won_tenders),
            "sector_focus": _analyze_sector_focus(won_tenders),
            "timing_patterns": _analyze_timing_patterns(won_tenders),
            "competition_analysis": _analyze_competition_levels(won_tenders),
        }

        return {
            "error": None,
            "company": company_info,
            "total_wins": len(won_tenders),
            "total_value": total_value,
            "country": country,
            "insights": insights,
        }

    except Exception as e:
        print(f"Error in strategy analysis: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "analysis_failed", "company": None, "insights": {}}
    finally:
        if should_close:
            db.close()


def _resolve_company(identifier: str, country: Optional[str], db) -> Optional[Dict]:
    """Find company by registry code or name."""
    query = (
        db.query(
            TenderResult.winner_name,
            TenderResult.winner_reg_code,
            func.count(TenderResult.procurement_id).label("total_wins"),
            func.sum(func.coalesce(TenderResult.contract_actual_cost, TenderResult.contract_cost)).label("total_value"),
        )
        .join(Tender, TenderResult.procurement_id == Tender.procurement_id)
        .filter(
            or_(
                TenderResult.winner_reg_code == identifier,
                TenderResult.winner_name.ilike(f"%{identifier}%"),
            ),
            TenderResult.winner_name.isnot(None),
            TenderResult.winner_name != "",
        )
    )
    if country:
        query = query.filter(Tender.country_code == country)

    result = (
        query.group_by(TenderResult.winner_name, TenderResult.winner_reg_code)
        .order_by(desc("total_wins"))
        .first()
    )

    if not result:
        return None

    return {
        "name": result[0],
        "reg_code": result[1] or "",
        "total_wins": result[2] or 0,
        "total_value": float(result[3] or 0),
    }


def _analyze_pricing_strategy(won_tenders: list) -> Dict:
    """Analyze pricing patterns from won contracts."""
    prices = []
    price_vs_estimate = []

    for result, tender, detail in won_tenders:
        contract_value = result.contract_actual_cost or result.contract_cost or 0
        if contract_value <= 0:
            continue
        prices.append(contract_value)

        estimated = detail.estimated_cost if detail else None
        if estimated and estimated > 0:
            ratio = contract_value / estimated
            price_vs_estimate.append(ratio)

    if not prices:
        return {"has_data": False}

    avg_price = sum(prices) / len(prices)
    median_price = sorted(prices)[len(prices) // 2]
    small = sum(1 for p in prices if p < 50000)
    medium = sum(1 for p in prices if 50000 <= p < 500000)
    large = sum(1 for p in prices if p >= 500000)

    avg_ratio = None
    pricing_tendency = "unknown"
    if price_vs_estimate:
        avg_ratio = sum(price_vs_estimate) / len(price_vs_estimate)
        if avg_ratio < 0.85:
            pricing_tendency = "aggressive_underbidding"
        elif avg_ratio < 0.95:
            pricing_tendency = "competitive"
        elif avg_ratio <= 1.05:
            pricing_tendency = "market_rate"
        else:
            pricing_tendency = "premium"

    return {
        "has_data": True,
        "avg_contract_value": avg_price,
        "median_contract_value": median_price,
        "min_value": min(prices),
        "max_value": max(prices),
        "brackets": {"small": small, "medium": medium, "large": large},
        "pricing_vs_estimate": {
            "avg_ratio": avg_ratio,
            "tendency": pricing_tendency,
            "sample_size": len(price_vs_estimate),
        },
    }


def _analyze_buyer_relationships(won_tenders: list) -> Dict:
    """Identify repeat buyer relationships."""
    buyer_wins: Dict[str, int] = {}
    buyer_values: Dict[str, float] = {}

    for result, tender, detail in won_tenders:
        authority = tender.contracting_authority_name or "Unknown"
        buyer_wins[authority] = buyer_wins.get(authority, 0) + 1
        buyer_values[authority] = buyer_values.get(authority, 0) + (
            result.contract_actual_cost or result.contract_cost or 0
        )

    repeat_buyers = [
        {
            "authority_name": name,
            "win_count": count,
            "total_value": buyer_values[name],
        }
        for name, count in sorted(buyer_wins.items(), key=lambda x: x[1], reverse=True)
        if count > 1
    ][:10]

    total_wins = len(won_tenders)
    repeat_win_count = sum(b["win_count"] for b in repeat_buyers)

    return {
        "has_data": len(buyer_wins) > 0,
        "total_unique_buyers": len(buyer_wins),
        "repeat_buyers": repeat_buyers,
        "repeat_buyer_count": len(repeat_buyers),
        "repeat_win_percentage": round(repeat_win_count / total_wins * 100, 1) if total_wins > 0 else 0,
        "one_time_buyers_count": sum(1 for c in buyer_wins.values() if c == 1),
    }


def _analyze_sector_focus(won_tenders: list) -> Dict:
    """Analyze CPV code and procurement type patterns."""
    cpv_wins: Dict[str, Dict] = {}
    type_wins = {"Services": 0, "Supplies": 0, "Works": 0, "Other": 0}
    type_map = {"T": "Services", "A": "Supplies", "E": "Works"}

    for result, tender, detail in won_tenders:
        cpv_code = detail.primary_cpv_code if detail else ""
        cpv_name = detail.primary_cpv_name if detail else "Unknown"

        if cpv_code:
            division = cpv_code[:2]
            if division not in cpv_wins:
                cpv_wins[division] = {"code": division, "name": cpv_name, "count": 0, "total_value": 0}
            cpv_wins[division]["count"] += 1
            cpv_wins[division]["total_value"] += (result.contract_actual_cost or result.contract_cost or 0)

        proc_type = tender.procurement_type or ""
        type_name = type_map.get(proc_type, "Other")
        type_wins[type_name] += 1

    top_sectors = sorted(cpv_wins.values(), key=lambda x: x["count"], reverse=True)[:8]
    total = sum(s["count"] for s in top_sectors)
    top_sector_share = top_sectors[0]["count"] / total * 100 if total > 0 and top_sectors else 0

    return {
        "has_data": len(top_sectors) > 0,
        "top_sectors": top_sectors,
        "procurement_types": {k: v for k, v in type_wins.items() if v > 0},
        "sector_concentration": round(top_sector_share, 1),
        "is_specialized": top_sector_share > 60,
        "total_sectors": len(cpv_wins),
    }


def _analyze_timing_patterns(won_tenders: list) -> Dict:
    """Analyze when the competitor wins (seasonal, frequency)."""
    quarterly_wins = {1: 0, 2: 0, 3: 0, 4: 0}
    yearly_wins: Dict[int, int] = {}

    for result, tender, detail in won_tenders:
        date = tender.created_at
        if not date:
            continue
        quarter = (date.month - 1) // 3 + 1
        quarterly_wins[quarter] += 1
        yearly_wins[date.year] = yearly_wins.get(date.year, 0) + 1

    peak_quarter = max(quarterly_wins, key=quarterly_wins.get) if any(quarterly_wins.values()) else None
    quarter_names = {1: "Q1 (Jan-Mar)", 2: "Q2 (Apr-Jun)", 3: "Q3 (Jul-Sep)", 4: "Q4 (Oct-Dec)"}

    sorted_years = sorted(yearly_wins.items())
    trend = "stable"
    if len(sorted_years) >= 2:
        recent = sorted_years[-1][1]
        previous = sorted_years[-2][1]
        if recent > previous * 1.2:
            trend = "growing"
        elif recent < previous * 0.8:
            trend = "declining"

    return {
        "has_data": len(yearly_wins) > 0,
        "quarterly_distribution": quarterly_wins,
        "peak_quarter": quarter_names.get(peak_quarter, "Unknown"),
        "yearly_wins": dict(sorted_years[-5:]) if sorted_years else {},
        "trend": trend,
    }


def _analyze_competition_levels(won_tenders: list) -> Dict:
    """Analyze competitive landscape for this company's wins."""
    offer_counts = []
    low_competition = 0
    high_competition = 0

    for result, tender, detail in won_tenders:
        if result.offer_count and result.offer_count > 0:
            offer_counts.append(result.offer_count)
            if result.offer_count <= 2:
                low_competition += 1
            if result.offer_count >= 5:
                high_competition += 1

    if not offer_counts:
        return {"has_data": False}

    total = len(offer_counts)
    return {
        "has_data": True,
        "avg_bidders": round(sum(offer_counts) / total, 1),
        "min_bidders": min(offer_counts),
        "max_bidders": max(offer_counts),
        "low_competition_wins": low_competition,
        "high_competition_wins": high_competition,
        "low_competition_pct": round(low_competition / total * 100, 1),
        "high_competition_pct": round(high_competition / total * 100, 1),
        "total_with_data": total,
    }
