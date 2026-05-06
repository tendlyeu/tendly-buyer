"""Canvas artifact for the 'legal_lookup' chat tool — renders an excerpt
from an Estonian/EU public-procurement legal source with a citation
back to the original URL."""

from fasthtml.common import Div, P, A, H2, H3, Span
from core.utils import _raw


def _md_to_html(text: str) -> str:
    """Tiny markdown helper — bold, line breaks, paragraphs, code-style refs."""
    import html, re
    s = html.escape(text or "")
    # Bold: **text**
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    # Italic: *text*
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", s)
    # Section refs (RHS §X, Article X)
    s = re.sub(r"(RHS\s*§\s*\d+[a-z\d⁰-⁹]*)", r'<code style="background:#eff6ff;color:#1e40af;padding:1px 6px;border-radius:4px;font-size:11px;">\1</code>', s)
    # Paragraphs (split on blank lines)
    paras = [p.strip() for p in s.split("\n\n") if p.strip()]
    return "".join(f"<p style='margin:0 0 10px;line-height:1.55;'>{p.replace(chr(10), '<br>')}</p>" for p in paras)


def legal_lookup_panel(data: dict, language: str = "en") -> Div:
    url = data.get("url") or ""
    question = data.get("question") or ""
    excerpt = data.get("excerpt") or ""

    # Pretty host label
    host = url.replace("https://", "").replace("http://", "").split("/")[0]

    return Div(
        # Header: badge + question
        Div(
            Div(
                _raw('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round"><path d="M3 6l9-4 9 4v6c0 5-3.5 9.5-9 11-5.5-1.5-9-6-9-11V6z"/></svg>'),
                style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;background:#f5f3ff;border-radius:50%;",
            ),
            Div(
                P("LEGAL LOOKUP", style="font-size:11px;color:#5b21b6;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin:0;"),
                H2(question or "Legal source", style="font-size:16px;font-weight:600;color:#111827;margin:2px 0 0;"),
            ),
            style="display:flex;align-items:center;gap:12px;padding:12px 14px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:10px;",
        ),

        # Body — the cited excerpt
        Div(
            _raw(_md_to_html(excerpt)),
            style="margin-top:14px;padding:14px;background:#fff;border:1px solid #f3f4f6;border-radius:10px;font-size:13px;color:#1f2937;",
        ),

        # Footer — citation
        Div(
            Span("Source: ", style="font-size:12px;color:#6b7280;"),
            A(host, href=url, target="_blank", rel="noopener noreferrer",
              style="font-size:12px;color:#2563eb;text-decoration:none;font-weight:500;word-break:break-all;"),
            style="margin-top:12px;padding-top:10px;border-top:1px solid #f3f4f6;",
        ),

        cls="detail-body",
        style="padding:14px;",
    )
