"""
main.py — FastAPI application for the IR Scraper System.
Endpoints:
  GET  /              → Serves frontend UI
  POST /scrape        → Finds IR page, scrapes links, downloads PDFs
  GET  /downloads/{f} → Serves a downloaded PDF file
"""

import asyncio
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright

from models import ScrapeRequest, ScrapeResponse, IRItem, ItemType, QuarterlyDocs, YearlyData
from scraper.http_scraper import scrape_ir_page_http
from scraper.playwright_scraper import scrape_ir_page
from scraper.pdf_downloader import download_or_print_pdf, DOWNLOADS_DIR

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="IR Scraper",
    description="Scrapes Investor Relations sites and downloads press releases & presentations as PDF.",
    version="1.0.0",
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Serve downloaded PDFs at /downloads/<filename>
app.mount("/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="downloads")


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_ui():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest, req: Request):
    """
    Full pipeline:
    1. Discover the IR page from the company URL
    2. Scrape press-release and presentation links
    3. Download/render each as a PDF
    4. Return structured results
    """
    source_url = request.source_url.strip()
    if not source_url.startswith("http"):
        source_url = "https://" + source_url

    ir_url = source_url

    # ── Helpers for filtering by year / quarter ─────────────────────────

    TARGET_YEARS = {2023, 2024, 2025, 2026}
    TARGET_QUARTERS = {1, 2, 3, 4}

    quarter_year_patterns = [
        # Q1 2024 / Q1-2024 / Q1'24
        re.compile(r"\bq([1-4])[\s\-–_]*('?)(\d{2}|\d{4})\b", re.IGNORECASE),
        # 1Q24 / 1Q 2024
        re.compile(r"\b([1-4])q[\s\-–_]*('?)(\d{2}|\d{4})\b", re.IGNORECASE),
        # 2024 Q1 / 2024-Q1
        re.compile(r"\b(\d{4})[\s\-–_]*q([1-4])\b", re.IGNORECASE),
        # First Quarter 2024 / 1st quarter 2024
        re.compile(r"\b(first|1st)\s+quarter\s+(\d{4})\b", re.IGNORECASE),
        re.compile(r"\b(second|2nd)\s+quarter\s+(\d{4})\b", re.IGNORECASE),
        re.compile(r"\b(third|3rd)\s+quarter\s+(\d{4})\b", re.IGNORECASE),
        re.compile(r"\b(fourth|4th)\s+quarter\s+(\d{4})\b", re.IGNORECASE),
    ]

    def _parse_year_quarter(text: str) -> Optional[Tuple[int, int]]:
        s = text.lower()
        for pat in quarter_year_patterns:
            m = pat.search(s)
            if not m:
                continue

            # Handle "2024 Q1"
            if pat.pattern.startswith(r"\b(\d{4})"):
                y = int(m.group(1))
                q = int(m.group(2))
                if y in TARGET_YEARS and q in TARGET_QUARTERS:
                    return y, q
                continue

            # Handle "First Quarter 2024" etc.
            if "quarter\\s+(\\d{4})" in pat.pattern:
                word = m.group(1).lower()
                y = int(m.group(2))
                q_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}
                q = q_map.get(word)
                if q and y in TARGET_YEARS and q in TARGET_QUARTERS:
                    return y, q
                continue

            # Handle Q1 2024 / 1Q24 variants
            q_str = m.group(1)
            y_str = m.group(3)
            try:
                q = int(q_str)
            except ValueError:
                continue
            if len(y_str) == 2:
                y = 2000 + int(y_str)
            else:
                y = int(y_str)
            if y in TARGET_YEARS and q in TARGET_QUARTERS:
                return y, q
        # Fallback: find a year with month/quarter terms if possible
        year_match = re.search(r"\b(2023|2024|2025|2026)\b", s)
        if year_match:
            year = int(year_match.group(1))

            month_map = {
                'jan': 1, 'feb': 1, 'mar': 1,
                'apr': 2, 'may': 2, 'jun': 2,
                'jul': 3, 'aug': 3, 'sep': 3,
                'oct': 4, 'nov': 4, 'dec': 4,
            }

            # month name + year (January 2024, Jan 2025)
            m = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(2023|2024|2025|2026)\b", s)
            if m:
                q = month_map.get(m.group(1)[:3])
                if q:
                    return year, q

            # date numerical patterns (2024-03-15, 03/15/2024)
            m = re.search(r"\b(2023|2024|2025|2026)[\/-](\d{1,2})[\/-](\d{1,2})\b", s)
            if m:
                month_num = int(m.group(2))
                if 1 <= month_num <= 12:
                    return year, (month_num - 1) // 3 + 1

            m = re.search(r"\b(\d{1,2})[\/-](\d{1,2})[\/-](2023|2024|2025|2026)\b", s)
            if m:
                month_num = int(m.group(1))
                if 1 <= month_num <= 12:
                    return year, (month_num - 1) // 3 + 1

            for mname, q in month_map.items():
                if mname in s:
                    return year, q

            # explicit quarter patterns
            for q in [1, 2, 3, 4]:
                if re.search(rf"\bq{q}\b|\b{q}.*q(uarter)?\b", s):
                    return year, q

            # special keywords fallback
            if 'proxy' in s:
                return year, 2
            if any(kw in s for kw in ['earnings', 'earnings call', 'quarterly results']):
                return year, 4
            if any(kw in s for kw in ['annual', 'annual meeting', 'annual shareholder']):
                return year, 4

            return year, 1
        return None

    ir_domain = urlparse(ir_url).netloc

    def _is_target_period(raw: Dict) -> bool:
        """
        Keep only PDFs for 2023–2026 Q1–Q4 based on title or link.
        Reject anything before 2023.
        """
        title = (raw.get("title") or "").lower()
        link = (raw.get("link") or "").lower()
        yq = _parse_year_quarter(title) or _parse_year_quarter(link)
        if yq:
            year, quarter = yq
            if year >= 2023 and year <= 2026 and quarter in (1, 2, 3, 4):
                return True
        return False

    def _priority(raw: Dict) -> int:
        link = (raw.get("link") or "").lower()
        title = (raw.get("title") or "").lower()
        s = f"{title} {link}"
        # prioritize by:
        #  1. target period (2023–2025, Q1–Q4)
        #  2. webcasts (audio)
        #  3. direct/document downloads
        #  4. presentations
        base = 0 if _is_target_period(raw) else 2
        if raw.get("item_type") == "webcast":
            return max(base - 1, 0)
        if ".pdf" in s or "download" in s:
            return base
        if "presentation" in s or "slides" in s:
            return base + 1
        if raw.get("item_type") == "presentation":
            return base + 2
        return base + 3

    async def _download_one(page, raw: Dict) -> str | None:
        # Per-item timeout so we don't hang forever on one URL.
        try:
            return await asyncio.wait_for(
                download_or_print_pdf(page=page, url=raw["link"], title=raw["title"]),
                timeout=20,
            )
        except Exception:
            return None

    def _create_item(raw: Dict, pdf_url: str | None = None, pdf_path: str | None = None) -> IRItem:
        """Helper to create IRItem with parsed year/quarter"""
        yq = _parse_year_quarter(raw.get("title", "") + " " + raw.get("link", ""))
        year, quarter = yq if yq else (None, None)
        return IRItem(
            title=raw["title"],
            link=raw["link"],
            item_type=ItemType(raw.get("item_type", "unknown")),
            pdf_path=pdf_path,
            pdf_url=pdf_url,
            parsed_year=year,
            parsed_quarter=quarter,
        )

    # ── Scrape + download PDFs (prefer Playwright; fallback to HTTP) ─────
    items: List[IRItem] = []
    used_playwright = False
    playwright_error = None
    max_downloads = 100  # allow up to 100 unique quarterly documents
    seen_links: set[str] = set()

    # Try Playwright first; fallback to HTTP scraper on failure
    raw_items: List[Dict] = []
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            raw_items = await scrape_ir_page(page, ir_url)
            await browser.close()
        used_playwright = True
        playwright_error = None
        print("[INFO] Playwright scraping used")
    except Exception as ex:
        used_playwright = False
        playwright_error = f"Playwright failed: {ex}. Falling back to HTTP scraper."
        print(f"[WARN] {playwright_error}")
        raw_items = await scrape_ir_page_http(ir_url)

    filtered = [r for r in raw_items if _is_target_period(r)]
    if filtered:
        raw_items = filtered
    raw_items = sorted(raw_items, key=_priority)
    
    for raw in raw_items:
        if len(items) >= max_downloads:
            break
        norm_link = (raw.get("link") or "").split("#", 1)[0]
        if norm_link in seen_links:
            continue

        pdf_url = None
        pdf_path = None

        if raw.get("item_type") == "webcast":
            # Webcast links are not downloaded as PDFs. Keep the link only.
            seen_links.add(norm_link)
            items.append(_create_item(raw, pdf_url=raw.get("link"), pdf_path=None))
            continue

        # determine if this link is PDF-like, to preserve previous behavior
        link_lower = (raw.get("link") or "").lower()
        is_pdf_link = link_lower.endswith(".pdf") or ".pdf" in link_lower

        if is_pdf_link:
            filename = await _download_one(None, raw)
            if filename:
                pdf_url = f"/downloads/{filename}"
                pdf_path = filename

        # Always append the item, even when downloading fails or is not a PDF
        seen_links.add(norm_link)
        items.append(_create_item(raw, pdf_url=pdf_url, pdf_path=pdf_path))

    # Build the years structure with default empty quarters (2023-2026)
    years_dict: Dict[int, Dict[str, QuarterlyDocs]] = {
        y: {f"quarter{i}": QuarterlyDocs() for i in range(1, 5)}
        for y in range(2023, 2027)
    }

    base_url = str(req.base_url).rstrip("/")

    def _resolve_link(pdf_url: str | None, link: str) -> str:
        if pdf_url and pdf_url.startswith("/downloads/"):
            return f"{base_url}{pdf_url}"
        return pdf_url or link

    def _make_title(year: int, quarter: int, doc_type: str, original_title: str) -> str:
        """Generate explicit title with quarter/year like 'Q1 2025 - Presentation'"""
        type_map = {
            "presentation": "Presentation",
            "press_release": "Press Release",
            "webcast": "Webcast",
            "transcript": "Transcript",
        }
        type_name = type_map.get(doc_type, doc_type.title())
        return f"Q{quarter} {year} - {type_name}"

    for item in items:
        # Use already-parsed year/quarter from item
        if item.parsed_year is None or item.parsed_quarter is None:
            continue
        year, quarter = item.parsed_year, item.parsed_quarter
        if year < 2023 or year > 2026 or quarter not in (1, 2, 3, 4):
            continue

        quarter_key = f"quarter{quarter}"
        docs = years_dict[year][quarter_key]

        if item.item_type == ItemType.presentation:
            docs.slides = _resolve_link(item.pdf_url, item.link)
            docs.slides_title = _make_title(year, quarter, "presentation", item.title)
        elif item.item_type == ItemType.press_release:
            docs.press_release = _resolve_link(item.pdf_url, item.link)
            docs.press_release_title = _make_title(year, quarter, "press_release", item.title)
        elif item.item_type == ItemType.webcast:
            docs.webcast_link = item.link
            docs.webcast_title = _make_title(year, quarter, "webcast", item.title)
        elif item.item_type == ItemType.transcript:
            docs.transcript = _resolve_link(item.pdf_url, item.link)
            docs.transcript_title = _make_title(year, quarter, "transcript", item.title)

    years = [YearlyData(year=y, quarters=q) for y, q in sorted(years_dict.items())]

    return ScrapeResponse(
        source_url=source_url,
        ir_page_url=ir_url,
        items=items,
        years=years,
        message=f"Downloaded {len(items)} PDF(s). (playwright={used_playwright})",
        playwright_used=used_playwright,
        playwright_error=playwright_error,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
