"""
ir_finder.py
Discovers the Investor Relations (IR) page URL from a company homepage.
Uses Playwright so JavaScript-rendered navigation menus are handled correctly.
"""

import re
from playwright.async_api import Page

# Keywords that strongly suggest an IR page
IR_KEYWORDS = [
    "investor relations", "investors", "investor", "ir",
    "financial news", "shareholder", "shareholders",
    "annual report", "sec filings", "earnings",
]


def _score_link(text: str, href: str) -> int:
    """Return a relevance score for a navigation link."""
    text_lower = text.lower().strip()
    href_lower = href.lower()
    score = 0
    for kw in IR_KEYWORDS:
        if kw in text_lower:
            score += 3
        if kw.replace(" ", "-") in href_lower or kw.replace(" ", "") in href_lower:
            score += 2
    return score


async def find_ir_page(page: Page, source_url: str) -> str | None:
    """
    Navigate to source_url and try to discover the IR page.
    Returns the IR page URL, or None if not found.
    """
    try:
        await page.goto(source_url, wait_until="domcontentloaded", timeout=30_000)
    except Exception:
        # Try with https:// prefix if bare domain was given
        if not source_url.startswith("http"):
            await page.goto(f"https://{source_url}", wait_until="domcontentloaded", timeout=30_000)
        else:
            raise

    # Collect all anchor tags
    links = await page.eval_on_selector_all(
        "a[href]",
        """(anchors) => anchors.map(a => ({
            text: a.innerText,
            href: a.href
        }))"""
    )

    best_score = 0
    best_href = None

    for link in links:
        href = link.get("href", "").strip()
        text = link.get("text", "").strip()
        if not href or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        score = _score_link(text, href)
        if score > best_score:
            best_score = score
            best_href = href

    return best_href if best_score >= 2 else None
