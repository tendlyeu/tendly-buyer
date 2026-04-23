"""Requirements artifact renderer for the canvas panel."""

import re
from fasthtml.common import *


# Requirement category colors
CATEGORY_STYLES = {
    "mandatory": ("#dc2626", "#fef2f2"),
    "exclusion": ("#dc2626", "#fef2f2"),
    "eligibility": ("#7c3aed", "#f5f3ff"),
    "technical": ("#2563eb", "#eff6ff"),
    "financial": ("#16a34a", "#f0fdf4"),
    "submission": ("#d97706", "#fffbeb"),
    "qualification": ("#ea580c", "#fff7ed"),
}


def requirements_panel(data: dict, language: str = "en"):
    """Render requirements as HTML for the canvas."""
    if not data:
        return Div(P("No data available."), cls="detail-body")

    tender_name = data.get("tender_name", "")
    ai_requirements = data.get("ai_requirements", "")
    authority = data.get("authority", "")
    cpv_code = data.get("cpv_code", "")
    cpv_name = data.get("cpv_name", "")

    sections = []

    # Header
    sections.append(Div(
        Div(tender_name, style="font-size:14px;font-weight:600;color:#111827;margin-bottom:4px;"),
        Div(authority, style="font-size:12px;color:#6b7280;margin-bottom:4px;"),
        *(
            [Div(f"CPV: {cpv_code} {cpv_name}", style="font-size:11px;color:#9ca3af;")]
            if cpv_code else []
        ),
        cls="detail-section",
    ))

    if not ai_requirements:
        sections.append(Div(
            P("No AI-extracted requirements available for this tender.",
              style="font-size:13px;color:#6b7280;font-style:italic;"),
            cls="detail-section",
        ))
        return Div(*sections, cls="detail-body", style="padding:20px;")

    # Parse requirements into sections
    parsed = _parse_requirements(ai_requirements)

    for section_name, items in parsed:
        color, bg = _get_category_style(section_name)
        req_items = []
        for item in items:
            req_items.append(Div(
                Span(style=f"display:inline-block;width:5px;height:5px;border-radius:50%;background:{color};margin-top:6px;flex-shrink:0;"),
                Span(item, style="font-size:13px;color:#374151;line-height:1.5;"),
                style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;",
            ))

        sections.append(Div(
            Div(
                Span(
                    section_name,
                    style=f"font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:{color};",
                ),
                Span(
                    str(len(items)),
                    style=f"font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;color:{color};background:{bg};",
                ),
                style="display:flex;align-items:center;gap:8px;margin-bottom:8px;",
            ),
            Div(*req_items),
            style=f"padding:12px;background:{bg};border-radius:10px;margin-bottom:8px;",
        ))

    return Div(*sections, cls="detail-body", style="padding:20px;")


def _parse_requirements(text: str):
    """Parse AI requirements text into categorized sections."""
    sections = []
    current_section = None
    current_items = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Check if this is a section header (all caps, or ends with colon)
        is_header = (
            line.isupper() and len(line) > 3 and len(line) < 80
        ) or (
            line.endswith(":") and not line.startswith("-") and not line.startswith("•")
        )

        if is_header:
            if current_section and current_items:
                sections.append((current_section, current_items))
            current_section = line.rstrip(":")
            current_items = []
        else:
            # Clean up list markers
            cleaned = re.sub(r"^[\-\•\*\d\.]+\s*", "", line).strip()
            if cleaned and len(cleaned) > 5:
                if current_section is None:
                    current_section = "Requirements"
                current_items.append(cleaned)

    if current_section and current_items:
        sections.append((current_section, current_items))

    # If no sections were found, treat everything as one block
    if not sections and text.strip():
        items = [
            re.sub(r"^[\-\•\*\d\.]+\s*", "", line).strip()
            for line in text.split("\n")
            if line.strip() and len(line.strip()) > 5
        ]
        if items:
            sections.append(("Requirements", items))

    return sections


def _get_category_style(section_name: str):
    """Get color and background for a requirement category."""
    name_lower = section_name.lower()
    for key, (color, bg) in CATEGORY_STYLES.items():
        if key in name_lower:
            return color, bg
    # Default
    return "#2563eb", "#eff6ff"
