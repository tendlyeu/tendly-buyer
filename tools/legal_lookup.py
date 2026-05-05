"""Legal lookup tool — fetches and summarises Estonian (and EU) public
procurement legal sources on demand so the chat can quote authoritative
text instead of paraphrasing from training data.

Allow-listed sources:
  * riigiteataja.ee  — Estonian Riigi Teataja (consolidated acts)
  * eur-lex.europa.eu — EU directives
  * fin.ee            — Estonian Ministry of Finance procurement policy
  * single-market-economy.ec.europa.eu — EU Commission procurement pages

The agent calls this when the user asks "what does RHS §X say?" or
"give me the legal basis for ...". The tool returns a focused excerpt
(via Gemini summarisation of the fetched page) that the chat can then
quote with a citation URL.
"""

import re
from typing import Dict
from urllib.parse import urlparse

from tools.registry import Tool, ToolResult, tool_registry


# Approved legal sources. Anything outside this list is rejected.
_ALLOWED_HOSTS = {
    "riigiteataja.ee", "www.riigiteataja.ee",
    "eur-lex.europa.eu",
    "fin.ee", "www.fin.ee",
    "single-market-economy.ec.europa.eu",
    "rik.ee", "www.rik.ee",
    "riigihanked.riik.ee",
}

# Curated quick-links for common queries so the agent doesn't need to
# guess the URL.
_TOPIC_URLS = {
    "rhs": "https://www.riigiteataja.ee/en/eli/505092017003/consolide",
    "public_procurement_act": "https://www.riigiteataja.ee/en/eli/505092017003/consolide",
    "riigihangete_seadus": "https://www.riigiteataja.ee/akt/505092017003",
    "thresholds": "https://www.fin.ee/en/public-procurement-state-aid-and-assets/public-procurement-policy",
    "eu_thresholds": "https://single-market-economy.ec.europa.eu/single-market/public-procurement/legal-rules-and-implementation/thresholds_en",
    "register": "https://riigihanked.riik.ee",
}


def _resolve_url(query: Dict) -> str:
    """Pick a URL from explicit `url` param, or a `topic` key, or guess
    from `keywords`."""
    url = (query.get("url") or "").strip()
    if url:
        return url
    topic = (query.get("topic") or "").strip().lower()
    if topic and topic in _TOPIC_URLS:
        return _TOPIC_URLS[topic]
    text = " ".join(query.get("keywords", [])).lower()
    if "riigihangete seadus" in text or "rhs" in text or "procurement act" in text:
        return _TOPIC_URLS["rhs"]
    if "threshold" in text or "piirmäär" in text:
        return _TOPIC_URLS["thresholds"]
    if "register" in text or "riigihanked" in text:
        return _TOPIC_URLS["register"]
    # Default to the act
    return _TOPIC_URLS["rhs"]


class LegalLookupTool(Tool):
    name = "legal_lookup"
    description = (
        "Fetch and summarise Estonian/EU public procurement legal sources "
        "(Riigi Teataja, EUR-Lex, fin.ee). Use when the user asks for the "
        "exact text of an act section, a current threshold value, or "
        "authoritative procedural guidance."
    )
    artifact_type = "legal_lookup"

    def execute(self, params: Dict, context: Dict) -> ToolResult:
        url = _resolve_url(params)

        # Allow-list check: only let the agent pull from approved
        # legal-information hosts.
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            host = ""
        if host not in _ALLOWED_HOSTS:
            return ToolResult(
                error=f"Refused to fetch {host}: not on the legal-source allow-list.",
                summary=(
                    "Tendly only fetches from official legal sources: "
                    "riigiteataja.ee, eur-lex.europa.eu, fin.ee, "
                    "single-market-economy.ec.europa.eu, rik.ee, "
                    "riigihanked.riik.ee."
                ),
            )

        question = (
            params.get("question")
            or params.get("rfp_description")
            or " ".join(params.get("keywords", []))
            or "Summarise the most relevant content for an Estonian public-sector procurement officer preparing a tender."
        )

        # Fetch the source. If the network blocks egress (sandbox / firewall)
        # or the site rejects the bot, fall back to the LLM's embedded
        # knowledge of Estonian public procurement law and still return
        # the canonical citation URL so the buyer can verify.
        from core.llm_client import LLMClient, LLMProvider
        text = None
        fetch_error = None
        try:
            import requests
            r = requests.get(url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0 (compatible; TendlyBuyerLegalLookup/1.0; +https://tendly.eu)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en,et;q=0.8",
            })
            if r.status_code == 200 and r.text:
                html = r.text[:200_000]
                text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
                text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()[:60_000]
            else:
                fetch_error = f"HTTP {r.status_code}"
        except Exception as e:
            fetch_error = str(e)

        llm = LLMClient(provider=LLMProvider.GEMINI, temperature=0.1)
        if text:
            prompt = (
                "You are extracting a precise excerpt from an authoritative "
                "Estonian / EU public procurement legal source for a buyer.\n\n"
                f"Source URL: {url}\n"
                f"User's question: {question}\n\n"
                "Source content:\n"
                f"{text}\n\n"
                "Return a focused answer with:\n"
                "1) A direct quote of the relevant section/article (with §, "
                "Article number, or paragraph reference) — verbatim from the text.\n"
                "2) One short paragraph (in the user's language) explaining "
                "what this means in practice for a buyer drafting a tender.\n"
                "3) The citation URL.\n\n"
                "Limit total to 350 words. If the source text doesn't contain "
                "an answer, say so honestly and suggest an alternative source."
            )
        else:
            prompt = (
                "You are answering an Estonian public-procurement legal "
                "question for a procurement officer. Live access to the "
                f"source ({url}) is currently unavailable ({fetch_error}). "
                "Use your knowledge of Riigihangete seadus (Public Procurement "
                "Act 2017) and EU Directive 2014/24/EU.\n\n"
                f"Question: {question}\n\n"
                "Return:\n"
                "1) The relevant section reference (e.g. RHS § X, Article Y) "
                "with a short paraphrase of the rule.\n"
                "2) One paragraph (in the user's language) explaining the "
                "practical implication for a buyer drafting a tender.\n"
                "3) Cite the canonical URL: " + url + "\n"
                "4) Add a brief note: 'Live source temporarily unavailable — "
                "please verify exact wording at the cited URL.'\n\n"
                "Limit total to 350 words. Never invent section numbers; if "
                "you're unsure, say 'see the cited source for the exact text'."
            )

        result = llm.chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=900)
        if not result.get("success"):
            return ToolResult(
                error=f"LLM summarisation failed: {result.get('error')}",
                summary=f"Could not produce a legal excerpt for {url}.",
            )

        excerpt = (result.get("content") or "").strip()

        return ToolResult(
            artifact_type="legal_lookup",
            artifact_id=f"legal_{abs(hash(url))%10**8}",
            artifact_data={
                "url": url,
                "question": question,
                "excerpt": excerpt,
            },
            summary=(
                f"Legal lookup from {url}:\n\n{excerpt[:1500]}"
            ),
        )


tool_registry.register(LegalLookupTool())
