# Intelvest — IR Scraper Backend

FastAPI backend that scrapes Investor Relations (IR) websites and returns:

- Press release PDFs
- Presentation PDFs & slides
- Webcast links (e.g. audio files like `.mp3`)
- All relevant document links (press release pages, investor news, etc.)

It uses **Playwright** (with HTTP fallback) for rendering JS-heavy IR sites and automatically downloads/serves PDFs under `/downloads`.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python run.py
```

API docs available at:
- `http://127.0.0.1:8001/docs`

## API

### POST `/scrape`

Scrapes a single IR page and returns extracted documents.

**Request:**
```json
{
  "source_url": "https://investors.3m.com/financials/quarterly-results/default.aspx"
}
```

**Response:**
```json
{
  "source_url": "...",
  "ir_page_url": "...",
  "items": [
    {
      "title": "Q4 2025 Earnings Infographic",
      "link": "https://...",
      "item_type": "presentation",
      "pdf_url": "/downloads/...",
      "parsed_year": 2025,
      "parsed_quarter": 4
    }
  ],
  "years": [...],
  "message": "Downloaded X PDF(s)",
  "playwright_used": true,
  "playwright_error": null
}
```

**Item Types:**
- `press_release` - Press releases and news announcements
- `presentation` - Presentation slides, decks, and supplemental materials
- `webcast` - Audio/video webcast links
- `transcript` - Earnings call transcripts
- `unknown` - Other documents (non-PDF links)

### Batch Testing

Test multiple IR sites at once using a batch JSON file.

**Batch JSON format:**
```json
{
  "batch": [
    {
      "ticker": "MMM",
      "url": "https://investors.3m.com/home/default.aspx"
    },
    {
      "ticker": "AAPL",
      "url": "https://investor.apple.com"
    }
  ]
}
```

**Run batch test:**
```bash
python test_ir_links.py sample_batch.json
```

This generates `batch_test_results.json` with detailed results for each site.

## Features

- **Dual-engine scraping:**
  - Primary: Playwright (handles JS-rendered content)
  - Fallback: HTTP + BeautifulSoup (lightweight, reliable)
  - Auto-selects based on site complexity
  
- **Smart timeouts:**
  - Page fetch: 15 seconds
  - PDF download: 20 seconds
  - Prevents hanging on slow/blocked sites

- **Comprehensive link capture:**
  - Extracts PDFs for download
  - Returns all document links (even non-PDF)
  - Parses year/quarter from titles

- **Batch processing:**
  - Test 10+ IR sites in one run
  - Generates summary reports
  - Per-site timing and success metrics

## Configuration

Key settings in codebase:
- `MAX_PAGES = 12` - Max pages to crawl per site (http_scraper.py)
- `PAGE_TIMEOUT = 15` - HTTP request timeout in seconds
- `DOWNLOAD_TIMEOUT = 20` - PDF download timeout per item
- Port: `8001` (see run.py)

## Project Structure

```
Intelvest/
├── main.py                    # FastAPI app, request handling
├── models.py                  # Pydantic models (ScrapeRequest, etc.)
├── run.py                     # Uvicorn server launcher
├── requirements.txt           # Python dependencies
├── scraper/
│   ├── http_scraper.py       # HTTP + BeautifulSoup scraper
│   ├── playwright_scraper.py # Playwright browser automation
│   └── pdf_downloader.py     # PDF fetch & download logic
├── test_ir_links.py          # Batch test script
├── quick_test.py             # Single-URL test script
└── downloads/                # Downloaded PDFs (auto-created)
```

## Example Usage

**Single URL (via Python):**
```python
import httpx

url = "https://investors.chubb.com"
response = httpx.post(
    "http://127.0.0.1:8001/scrape",
    json={"source_url": url},
    timeout=180
)
print(response.json())
```

**Batch (via CLI):**
```bash
python test_ir_links.py sample_batch.json
# Results saved to batch_test_results.json
```

## Performance Notes

- Average response time: 1-10 seconds per site (varies by site size)
- Batch of 10 sites: typically 30-60 seconds total
- Large IR sites may take longer due to crawl depth

## Troubleshooting

**Q: Why is `playwright_used` false?**
- A: Site may have triggered Playwright error, fell back to HTTP scraper. Check `playwright_error` field for details.

**Q: No PDF downloaded for a valid PDF link?**
- A: Link may be behind redirect, require authentication, or match non-target-period filters.

**Q: Response is slow?**
- A: Large IR sites with many pages/links take longer to crawl. Try a specific URL path instead of home page.

## License

MIT

