"""
playwright_scraper.py
Scrapes press release and presentation links from an IR page using Playwright
for rendering and BeautifulSoup (bs4) for HTML parsing.
"""

from typing import List, Dict
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page

# Keywords that identify a press-release link
PRESS_RELEASE_KEYWORDS = [
    "press release",
    "press-release",
    "news release",
    "media release",
    "newsroom",
    "news",
    "announcements",
    "announcement",
]

# Keywords that identify a webcast link
WEBCAST_KEYWORDS = [
    "webcast",
    "earnings call",
    "conference call",
    "audio webcast",
]

# Keywords that identify a presentation link (PDF slides, decks, etc.)
PRESENTATION_KEYWORDS = [
    "presentation",
    "slides",
    "deck",
    "supplemental information",
    "supplemental data",
    "investor day",
    "annual report",
    "quarterly report",
    "conference",
    "roadshow",
    "analyst",
]


def _is_pdf_href(href: str) -> bool:
    """
    Return True if the URL path looks like a PDF, even if there is a query
    string (e.g. '?disposition=inline').
    """
    try:
        parsed = urlparse(href)
    except Exception:
        return href.lower().endswith(".pdf")
    return parsed.path.lower().endswith(".pdf")


def _is_audio_href(href: str) -> bool:
    """
    Return True if the URL path looks like an audio/webcast file (e.g. .mp3).
    """
    try:
        parsed = urlparse(href)
    except Exception:
        path = href
    else:
        path = parsed.path
    path = path.lower()
    return path.endswith(".mp3") or path.endswith(".m4a") or path.endswith(".wav")


def _classify_link(text: str, href: str) -> str:
    """Return 'press_release', 'presentation', 'webcast', or 'unknown'."""
    combined = (text + " " + href).lower()
    if any(kw in combined for kw in PRESS_RELEASE_KEYWORDS):
        return "press_release"
    if any(kw in combined for kw in WEBCAST_KEYWORDS):
        return "webcast"
    if any(kw in combined for kw in PRESENTATION_KEYWORDS):
        return "presentation"
    # Treat direct PDF links as potential documents (handle '?disposition=inline')
    if _is_pdf_href(href):
        return "presentation"
    # Treat direct audio links as webcasts
    if _is_audio_href(href):
        return "webcast"
    return "unknown"


async def _scroll_to_bottom(page: Page) -> None:
    """Scroll to trigger lazy-loaded content."""
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await page.wait_for_timeout(600)


async def _collect_links(page: Page) -> List[Dict]:
    """
    Return all anchors with href from the current page, using BeautifulSoup
    on the fully rendered HTML provided by Playwright.
    """
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    base_url = page.url
    links: List[Dict] = []

    for a in soup.find_all("a", href=True):
        raw_text = a.get_text(strip=True) or a.get("title") or a.get("aria-label") or ""
        text = raw_text.strip()
        href = urljoin(base_url, a["href"])
        links.append({"text": text, "href": href})

    return links


async def scrape_ir_page(page: Page, ir_url: str) -> List[Dict]:
    """
    Navigate to `ir_url` and collect press-release + presentation links.

    Returns a list of dicts:
      {title: str, link: str, item_type: str}
    """
    await page.goto(ir_url, wait_until="domcontentloaded", timeout=40_000)
    await _scroll_to_bottom(page)

    raw_links = await _collect_links(page)

    seen = set()
    results: List[Dict] = []

    for lnk in raw_links:
        href: str = lnk.get("href", "").strip()
        text: str = lnk.get("text", "").strip()

        if not href or href in seen:
            continue
        if href.startswith("mailto:") or href.startswith("tel:") or href == "#":
            continue
        # Skip anchors that go back to the same IR page root (nav links)
        if href == ir_url or href == ir_url.rstrip("/") + "/":
            continue

        item_type = _classify_link(text, href)
        if item_type == "unknown":
            continue

        seen.add(href)
        results.append(
            {
                "title": text or href.split("/")[-1],
                "link": href,
                "item_type": item_type,
            }
        )

    # Also look for sub-pages linked from the IR page that might have full lists
    sub_pages = await _find_sub_pages(page, ir_url, raw_links)
    for sub_url in sub_pages:
        try:
            await page.goto(sub_url, wait_until="domcontentloaded", timeout=30_000)
            await _scroll_to_bottom(page)
            sub_links = await _collect_links(page)
            for lnk in sub_links:
                href = lnk.get("href", "").strip()
                text = lnk.get("text", "").strip()
                if not href or href in seen:
                    continue
                if href.startswith("mailto:") or href.startswith("tel:") or href == "#":
                    continue
                item_type = _classify_link(text, href)
                if item_type == "unknown":
                    continue
                seen.add(href)
                results.append(
                    {
                        "title": text or href.split("/")[-1],
                        "link": href,
                        "item_type": item_type,
                    }
                )
        except Exception:
            continue

    return results


async def _find_sub_pages(page: Page, ir_url: str, raw_links: List[Dict]) -> List[str]:
    """Find IR sub-pages worth scraping (press-release section, presentations section)."""
    SUB_PAGE_KEYWORDS = [
        "press-release",
        "press release",
        "news",
        "presentations",
        "events",
        "reports",
        "filings",
        "publications",
    ]

    ir_domain = urlparse(ir_url).netloc
    sub_pages: List[str] = []
    seen = {ir_url}

    for lnk in raw_links:
        href = lnk.get("href", "").strip()
        text = (lnk.get("text", "") or "").lower()
        if not href:
            continue
        try:
            parsed = urlparse(href)
        except Exception:
            continue
        if parsed.netloc and parsed.netloc != ir_domain:
            continue
        combined = (text + " " + href).lower()
        if any(kw in combined for kw in SUB_PAGE_KEYWORDS) and href not in seen:
            seen.add(href)
            sub_pages.append(href)

    return sub_pages[:5]  # limit to 5 sub-pages to avoid excessive crawling
