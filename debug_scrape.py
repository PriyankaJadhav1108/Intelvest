import asyncio

from playwright.async_api import async_playwright


async def inspect(url: str) -> None:
    from scraper.playwright_scraper import _collect_links  # type: ignore

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40_000)
        await page.wait_for_timeout(5000)
        links = await _collect_links(page)
        print(f"Total links: {len(links)}")
        print("Links containing 'pdf' or 'quarter' or 'earnings' or 'results':")
        for l in links:
            txt = (l.get("text") or "")[:120]
            href = l.get("href") or ""
            lower = (txt + " " + href).lower()
            if any(k in lower for k in ["pdf", "quarter", "earnings", "results"]):
                print("-", txt, "->", href)
        await browser.close()


async def main():
    urls = [
        "https://ir.tesla.com/#quarterly-disclosure",
        "https://ir.kraftheinzcompany.com/financials/quarterly-results",
    ]
    for u in urls:
        print("=" * 80)
        await inspect(u)


if __name__ == "__main__":
    asyncio.run(main())

