"""
http_scraper.py
Scrapes press release and presentation PDF links from an IR page using
plain HTTP (httpx) + BeautifulSoup, without Playwright.
"""

from collections import deque
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


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

WEBCAST_KEYWORDS = [
    "webcast",
    "earnings call",
    "conference call",
    "audio webcast",
]

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
    try:
        parsed = urlparse(href)
    except Exception:
        return href.lower().endswith(".pdf")
    return parsed.path.lower().endswith(".pdf")


def _is_audio_href(href: str) -> bool:
    try:
        parsed = urlparse(href)
    except Exception:
        path = href
    else:
        path = parsed.path
    path = path.lower()
    return path.endswith(".mp3") or path.endswith(".m4a") or path.endswith(".wav")


def _classify_link(text: str, href: str) -> str:
    combined = (text + " " + href).lower()
    if any(kw in combined for kw in PRESS_RELEASE_KEYWORDS):
        return "press_release"
    if any(kw in combined for kw in WEBCAST_KEYWORDS) or _is_audio_href(href):
        return "webcast"
    if any(kw in combined for kw in PRESENTATION_KEYWORDS):
        return "presentation"
    if _is_pdf_href(href):
        return "presentation"
    return "unknown"


def _should_follow_link(text: str, href: str) -> Optional[str]:
    """
    Return an item_type hint ('press_release'|'presentation') if this looks like
    a relevant section page worth crawling; otherwise None.
    """
    combined = (text + " " + href).lower()
    # strong section hints
    if any(k in combined for k in ["events", "presentations", "webcasts", "slides", "earnings", "quarterly"]):
        return "presentation"
    if any(k in combined for k in ["press", "press releases", "news", "newsroom", "announcements"]):
        return "press_release"
    # fallback to classifier
    t = _classify_link(text, href)
    return t if t != "unknown" else None


async def scrape_ir_page_http(ir_url: str) -> List[Dict]:
    """
    Fetch `ir_url` over HTTP and collect press-release + presentation PDF links.
    Crawls a small number of relevant sub-pages (news/events/presentations)
    so we can return actual PDF links rather than section URLs.

    Returns a list of dicts:
      {title: str, link: str, item_type: str}
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    root = urlparse(ir_url)
    root_netloc = root.netloc

    def _same_site(url: str) -> bool:
        try:
            return urlparse(url).netloc == root_netloc
        except Exception:
            return False

    results: List[Dict] = []
    seen_links: set[str] = set()
    visited_pages: set[str] = set()

    # (url, depth, type_hint)
    q: deque[Tuple[str, int, Optional[str]]] = deque()
    q.append((ir_url, 0, None))

    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        while q and len(visited_pages) < 12 and len(results) < 300:
            url, depth, hint = q.popleft()
            if url in visited_pages:
                continue
            if not _same_site(url):
                continue
            visited_pages.add(url)

            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href_raw = a["href"].strip()
                href = urljoin(url, href_raw)
                text = (a.get_text(strip=True) or a.get("title") or a.get("aria-label") or "").strip()

                if not href or href.startswith("mailto:") or href.startswith("tel:") or href == "#":
                    continue

                if href in seen_links:
                    continue
                seen_links.add(href)

                # Collect strong candidates for document / audio downloads.
                # Many IR platforms use download endpoints that do not end with ".pdf".
                item_type = hint or _classify_link(text, href)
                combined = (text + " " + href).lower()
                is_doc_candidate = (
                    _is_pdf_href(href)
                    or "pdf" in combined
                    or "download" in combined
                    or "presentation" in combined
                    or "slides" in combined
                    or _is_audio_href(href)
                )
                if item_type != "unknown" and is_doc_candidate:
                    results.append(
                        {
                            "title": text or href.split("/")[-1],
                            "link": href,
                            "item_type": item_type if item_type != "unknown" else "presentation",
                        }
                    )

                # Follow likely section pages to discover PDFs
                if depth < 2 and _same_site(href):
                    t_hint = _should_follow_link(text, href)
                    if t_hint:
                        q.append((href, depth + 1, t_hint))

    return results

