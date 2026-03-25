"""
pdf_downloader.py
Downloads PDFs from direct .pdf links or prints HTML pages to PDF via Playwright.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional

import httpx
from playwright.async_api import Page
from urllib.parse import urlparse

DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(url: str, title: str, ext: str = ".pdf") -> str:
    """Generate a safe, unique filename from a URL or title."""
    slug = re.sub(r"[^\w\-]", "_", title[:60]).strip("_")
    uid = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{slug}_{uid}{ext}"


def _is_pdf_url(url: str) -> bool:
    """
    Return True if the URL points to a PDF, including patterns like:
      - https://example.com/file.pdf
      - https://example.com/file.pdf?download=1
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return url.lower().endswith(".pdf")
    return parsed.path.lower().endswith(".pdf")

async def _download_maybe_pdf(url: str, output_path: Path, filename: str) -> Optional[str]:
    """
    Download a URL that might be a PDF even if it does not end with .pdf.
    Validates using content-type, content-disposition, and PDF magic bytes.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        async with client.stream("GET", url, headers=headers) as response:
            if response.status_code != 200:
                print(f"[pdf_downloader] HTTP {response.status_code} for {url}")
                return None

            content_type = (response.headers.get("content-type") or "").lower()
            content_disp = (response.headers.get("content-disposition") or "").lower()

            first_chunk = b""
            async for chunk in response.aiter_bytes(chunk_size=8192):
                first_chunk = chunk
                break

            looks_like_pdf = (
                "application/pdf" in content_type
                or ".pdf" in content_disp
                or first_chunk.startswith(b"%PDF-")
            )
            if not looks_like_pdf:
                return None

            with open(output_path, "wb") as f:
                if first_chunk:
                    f.write(first_chunk)
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
    return filename


async def download_or_print_pdf(
    page: Optional[Page],
    url: str,
    title: str,
) -> Optional[str]:
    """
    Download or render a page as PDF.

    - If the URL ends with '.pdf' → download bytes directly via httpx.
    - Otherwise → navigate with Playwright and use page.pdf() to print to PDF.

    Returns the relative filename (e.g. 'press_release_abc123.pdf'),
    or None on failure.
    """
    filename = _safe_filename(url, title)
    output_path = DOWNLOADS_DIR / filename

    if output_path.exists():
        return filename  # already downloaded

    try:
        if _is_pdf_url(url):
            return await _download_direct_pdf(url, output_path, filename)
        # If no Playwright page is available, only direct PDF downloads are supported.
        if page is None:
            return await _download_maybe_pdf(url, output_path, filename)
        return await _print_page_to_pdf(page, url, output_path, filename)
    except Exception as exc:
        print(f"[pdf_downloader] Failed for {url}: {exc}")
        return None


async def _download_direct_pdf(url: str, output_path: Path, filename: str) -> Optional[str]:
    """Stream-download a remote PDF file."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        async with client.stream("GET", url, headers=headers) as response:
            if response.status_code != 200:
                print(f"[pdf_downloader] HTTP {response.status_code} for {url}")
                return None
            content_type = response.headers.get("content-type", "")
            # Accept PDFs and octet-stream (some servers send PDF as binary)
            if "pdf" not in content_type and "octet-stream" not in content_type and "application" not in content_type:
                # Try anyway if URL ends with .pdf
                pass
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
    return filename


async def _print_page_to_pdf(page: Page, url: str, output_path: Path, filename: str) -> Optional[str]:
    """Use Playwright's built-in PDF printer to render an HTML page as PDF."""
    await page.goto(url, wait_until="networkidle", timeout=15_000)
    # Scroll so content loads
    for _ in range(3):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await page.wait_for_timeout(500)
    await page.pdf(
        path=str(output_path),
        format="A4",
        print_background=True,
        margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
    )
    return filename
