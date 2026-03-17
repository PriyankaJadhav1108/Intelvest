# Intelvest — IR Scraper Backend

FastAPI backend that scrapes Investor Relations (IR) websites and returns:

- Press release PDFs
- Presentation PDFs
- Webcast links (e.g. audio files like `.mp3`)

It uses Playwright for JS-rendered IR sites and downloads/serves PDFs under `/downloads`.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python run.py
```

Open API docs at:

- `http://127.0.0.1:8000/docs`

## API

### POST `/scrape`

Request body:

```json
{ "source_url": "https://investor.uber.com/home/default.aspx" }
```

Response:

- `items[].item_type` is one of: `press_release`, `presentation`, `webcast`
- `items[].pdf_url` is:
  - `/downloads/<file>.pdf` for downloaded PDFs
  - the original webcast URL for `webcast`

