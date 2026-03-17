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

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright

from models import ScrapeRequest, ScrapeResponse, IRItem, ItemType
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
async def scrape(request: ScrapeRequest):
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

    TARGET_YEARS = {2023, 2024, 2025}
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
        return None

    ir_domain = urlparse(ir_url).netloc

    def _is_target_period(raw: Dict) -> bool:
        """
        Keep only PDFs for 2023–2025 Q1–Q4 based on title or link.
        For Uber (investor.uber.com) we enforce this filter strictly.
        For other IR sites, we accept all items and only use this
        information for prioritization.
        """
        title = (raw.get("title") or "").lower()
        link = (raw.get("link") or "").lower()
        if _parse_year_quarter(title) or _parse_year_quarter(link):
            return True
        # Only enforce the strict filter on Uber's IR domain
        if ir_domain == "investor.uber.com":
            return False
        # For other domains, don't filter items out solely due to
        # missing explicit quarter/year text.
        return True

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
                timeout=45,
            )
        except Exception:
            return None

    # ── Scrape + download PDFs (prefer Playwright; fallback to HTTP) ─────
    items: List[IRItem] = []
    used_playwright = False
    max_downloads = 50  # allow up to 50 unique quarterly PDFs
    seen_links: set[str] = set()

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            raw_items = await scrape_ir_page(page, ir_url)
            used_playwright = True

            # Prefer target 2023–2025 Q1–Q4 items; if none, fall back to all.
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
                # Webcasts: return the streaming URL directly (no PDF required)
                if raw.get("item_type") == "webcast":
                    seen_links.add(norm_link)
                    items.append(
                        IRItem(
                            title=raw["title"],
                            link=raw["link"],
                            item_type=ItemType.webcast,
                            pdf_path=None,
                            pdf_url=raw["link"],
                        )
                    )
                    continue

                filename = await _download_one(page, raw)
                if not filename:
                    continue
                seen_links.add(norm_link)
                items.append(
                    IRItem(
                        title=raw["title"],
                        link=raw["link"],
                        item_type=ItemType(raw["item_type"]),
                        pdf_path=filename,
                        pdf_url=f"/downloads/{filename}",
                    )
                )

            await page.close()
            await browser.close()
    except Exception:
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
            if raw.get("item_type") == "webcast":
                seen_links.add(norm_link)
                items.append(
                    IRItem(
                        title=raw["title"],
                        link=raw["link"],
                        item_type=ItemType.webcast,
                        pdf_path=None,
                        pdf_url=raw["link"],
                    )
                )
                continue

            filename = await _download_one(None, raw)
            if not filename:
                continue
            seen_links.add(norm_link)
            items.append(
                IRItem(
                    title=raw["title"],
                    link=raw["link"],
                    item_type=ItemType(raw["item_type"]),
                    pdf_path=filename,
                    pdf_url=f"/downloads/{filename}",
                )
            )

    return ScrapeResponse(
        source_url=source_url,
        ir_page_url=ir_url,
        items=items,
        message=f"Downloaded {len(items)} PDF(s). (playwright={used_playwright})",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
