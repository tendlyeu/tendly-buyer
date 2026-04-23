"""Canvas panel component — the right pane for artifacts."""

from fasthtml.common import *
from core.utils import _raw


# Close icon SVG
_ICON_CLOSE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>'


def canvas_panel():
    """Empty canvas shell — populated via JS when artifacts arrive.

    The canvas starts hidden (display:none). When an artifact SSE event
    arrives, JS calls openCanvas() which fetches the server-rendered HTML
    fragment and inserts it into #canvas-body.
    """
    return Div(
        # Header with title and close button
        Div(
            Div(
                Span("", id="canvas-title", cls="canvas-header-title"),
                cls="canvas-header-left",
            ),
            Button(
                _raw(_ICON_CLOSE),
                cls="canvas-close-btn",
                onclick="closeCanvas()",
            ),
            cls="canvas-header",
            id="canvas-header",
        ),
        # Scrollable body where artifact HTML is injected
        Div(
            id="canvas-body",
            cls="canvas-body",
        ),
        cls="canvas-panel",
        id="canvas-panel",
    )
