"""AI requirements formatting component."""

from fasthtml.common import *
from core.utils import _raw


_REQ_SECTION_CONFIG = {
    # Estonian headers (with special characters)
    'KOHUSTUSLIKUD N\u00d5UDED': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'KOHUSTUSLIKUD NOUDED': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'KOHUSTUSLIKUD KORVALDAMISE ALUSED': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    # English mandatory
    'MANDATORY EXCLUSION GROUNDS': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'MANDATORY QUALIFICATIONS': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'MANDATORY REQUIREMENTS': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    # Compliance / eligibility
    'VASTAVUSN\u00d5UDED': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'VASTAVUSNOUDED': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'ELIGIBILITY REQUIREMENTS': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'COMPLIANCE REQUIREMENTS': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    # Technical
    'TEHNILISED N\u00d5UDED': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'TEHNILISED NOUDED': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'TEHNILISED VOIMEKUSE NOUDED': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'TECHNICAL REQUIREMENTS': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'TECHNICAL CAPABILITY REQUIREMENTS': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    # Financial
    'FINANTSN\u00d5UDED': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'FINANTSNOUDED': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'FINANCIAL REQUIREMENTS': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'ECONOMIC AND FINANCIAL STANDING': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'MAJANDUSLIK JA FINANTSSEISUNDI N\u00d5UDED': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    # Submission
    'ESITAMISE N\u00d5UDED': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    'ESITAMISE NOUDED': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    'SUBMISSION REQUIREMENTS': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    'PROFESSIONAL REQUIREMENTS': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    # Qualification
    'QUALIFICATION REQUIREMENTS': {'color': '#0891b2', 'bg': '#ecfeff', 'border': '#a5f3fc', 'type': 'qualification'},
    'KVALIFIKATSIOONIN\u00d5UDED': {'color': '#0891b2', 'bg': '#ecfeff', 'border': '#a5f3fc', 'type': 'qualification'},
    'KVALIFIKATSIOONINOUDED': {'color': '#0891b2', 'bg': '#ecfeff', 'border': '#a5f3fc', 'type': 'qualification'},
    'SELECTION CRITERIA': {'color': '#0891b2', 'bg': '#ecfeff', 'border': '#a5f3fc', 'type': 'qualification'},
    'VALIKUKRITEERIUMID': {'color': '#0891b2', 'bg': '#ecfeff', 'border': '#a5f3fc', 'type': 'qualification'},
    # Latvian headers
    'OBLIG\u0100T\u0100S PRAS\u012aBAS': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'ATBILST\u012aBAS PRAS\u012aBAS': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'TEHNISK\u0100S PRAS\u012aBAS': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'FINAN\u0160U PRAS\u012aBAS': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'IESNIEG\u0160ANAS PRAS\u012aBAS': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    # Polish headers
    'WYMAGANIA OBOWI\u0104ZKOWE': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'WYMAGANIA ZGODNO\u015aCI': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'WYMAGANIA TECHNICZNE': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'WYMAGANIA FINANSOWE': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'WYMAGANIA DOTYCZ\u0104CE SK\u0141ADANIA': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    # Lithuanian headers
    'PRIVALOMIEJI REIKALAVIMAI': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'ATITIKTIES REIKALAVIMAI': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'TECHNINIAI REIKALAVIMAI': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'FINANSINIAI REIKALAVIMAI': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'PATEIKIMO REIKALAVIMAI': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
    # French headers
    'EXIGENCES OBLIGATOIRES': {'color': '#dc2626', 'bg': '#fef2f2', 'border': '#fecaca', 'type': 'mandatory'},
    'EXIGENCES DE CONFORMIT\u00c9': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'type': 'compliance'},
    'EXIGENCES TECHNIQUES': {'color': '#16a34a', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'type': 'technical'},
    'EXIGENCES FINANCI\u00c8RES': {'color': '#d97706', 'bg': '#fefce8', 'border': '#fde047', 'type': 'financial'},
    'EXIGENCES DE SOUMISSION': {'color': '#7c3aed', 'bg': '#faf5ff', 'border': '#e9d5ff', 'type': 'submission'},
}

_REQ_TYPE_ICONS = {
    'mandatory': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    'compliance': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15l2 2 4-4"/></svg>',
    'technical': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.6 9a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
    'financial': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    'submission': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    'qualification': '<svg width="14" height="14" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>',
}


def format_requirements_component(text):
    """Parse AI requirements text into color-coded FastHTML section cards."""
    if not text:
        return None

    # Pre-process: if text is mostly a single line with "* " delimiters,
    # split on "* " to convert to newline-separated format.
    # This handles the DB format: "* HEADER * item * item * HEADER * item"
    raw_lines = text.strip().split('\n')
    if len(raw_lines) <= 3 and '* ' in text:
        # Single-line or few-line format with * delimiters
        parts = text.split('* ')
        expanded = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Check if this part is a known section header
            part_upper = part.upper().rstrip('*').strip()
            is_known_header = any(h in part_upper for h in _REQ_SECTION_CONFIG)
            if is_known_header:
                expanded.append(f'* {part.rstrip("*").strip()}')
            else:
                expanded.append(f'- {part}')
        raw_lines = expanded

    lines = raw_lines
    sections = []
    current_header = None
    current_items = []

    def flush():
        nonlocal current_header, current_items
        if current_header and current_items:
            config = _REQ_SECTION_CONFIG.get(current_header, {'color': '#6b7280', 'bg': '#f9fafb', 'border': '#e5e7eb', 'type': 'other'})
            sections.append({'header': current_header, 'items': list(current_items), **config})
        current_header = None
        current_items = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        is_header = False
        line_upper = line.upper()
        for header in _REQ_SECTION_CONFIG:
            if header in line_upper:
                flush()
                current_header = header
                is_header = True
                break
        if is_header:
            continue
        if line.startswith('* ') or line.startswith('- '):
            item_text = line[2:].strip()
            if item_text and current_header:
                current_items.append(item_text)
        elif current_header and line:
            current_items.append(line)

    flush()

    if not sections:
        # No structured sections found - return plain text with basic formatting
        return Div(text, cls="detail-field-value", style="font-size:13.5px;line-height:1.6;white-space:pre-line;")

    # Reorder: submission first
    submission = [s for s in sections if s['type'] == 'submission']
    others = [s for s in sections if s['type'] != 'submission']
    ordered = submission + others

    cards = []
    for idx, section in enumerate(ordered):
        color = section['color']
        bg = section['bg']
        border = section['border']
        req_type = section['type']
        section_id = f"req-sec-{idx}"

        # Get type-specific icon
        icon_template = _REQ_TYPE_ICONS.get(req_type, _REQ_TYPE_ICONS.get('compliance'))
        icon_svg = icon_template.format(color=color) if icon_template else ''

        # Build visible items (first 3) and hidden items
        MAX_VISIBLE = 3
        visible = []
        hidden = []
        for i, item in enumerate(section['items']):
            item_div = Div(
                Span("--", cls="req-item-bullet", style=f"color:{color};"),
                Span(item),
                cls="req-item",
            )
            if i < MAX_VISIBLE:
                visible.append(item_div)
            else:
                hidden.append(item_div)

        children = [
            # Header
            Div(
                Div(_raw(icon_svg), cls="req-section-icon", style=f"background:{bg};color:{color};"),
                Span(section['header'], cls="req-section-title", style=f"color:{color};"),
                Span(str(len(section['items'])), cls="req-section-count", style=f"background:{bg};color:{color};"),
                cls="req-section-header",
            ),
            # Visible items
            *visible,
        ]

        if hidden:
            extra = len(hidden)
            children.append(
                Div(*hidden, id=f"{section_id}-hidden", style="display:none;")
            )
            children.append(
                NotStr(f'<button onclick="toggleReqItems(\'{section_id}\')" id="{section_id}-btn" data-show-more="Show {extra} more" data-show-less="Show less" class="req-show-more-btn">Show {extra} more</button>')
            )

        cards.append(
            Div(*children, cls="req-section", style=f"background:{bg};border:1px solid {border};")
        )

    return Div(*cards)
