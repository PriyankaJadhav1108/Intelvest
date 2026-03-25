import asyncio
import httpx
import json
import sys

async def test_url(ticker, url):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://127.0.0.1:8001/scrape",
                json={"source_url": url},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                return {
                    "ticker": ticker,
                    "url": url,
                    "status": "success",
                    "items_count": len(items),
                    "items": items
                }
            else:
                return {
                    "ticker": ticker,
                    "url": url,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
    except Exception as e:
        return {
            "ticker": ticker,
            "url": url,
            "status": "error",
            "error": str(e)
        }

async def main():
    if len(sys.argv) != 2:
        print("Usage: python test_ir_links.py <batch_json_file>")
        print("Example batch JSON format:")
        print('''{
  "batch": [
    {"ticker": "MMM", "url": "https://investors.3m.com"},
    {"ticker": "BLK", "url": "https://ir.blackrock.com"}
  ]
}''')
        return

    batch_file = sys.argv[1]
    try:
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)
    except Exception as e:
        print(f"Error reading batch file: {e}")
        return

    batch = batch_data.get("batch", [])
    if not batch:
        print("No batch data found in file")
        return

    results = []
    print(f"Testing {len(batch)} IR sites...\n")

    for i, item in enumerate(batch, 1):
        ticker = item.get("ticker", "Unknown")
        url = item.get("url", "")
        print(f"[{i}/{len(batch)}] Testing {ticker} - {url}...")

        result = await test_url(ticker, url)
        results.append(result)

        if result["status"] == "success":
            items_count = result["items_count"]
            print(f"  ✅ Success: {items_count} items found")
            if items_count > 0:
                # Show first few item types
                item_types = [item.get("item_type", "unknown") for item in result["items"][:3]]
                print(f"     Types: {', '.join(item_types)}")
        else:
            print(f"  ❌ Error: {result['error']}")

        print()

    # Save detailed results
    with open("batch_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    print("═" * 50)
    print("SUMMARY")
    print("═" * 50)
    print(f"Total sites tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Success rate: {len(successful)/len(results)*100:.1f}%")

    if successful:
        total_items = sum(r["items_count"] for r in successful)
        print(f"Total items found: {total_items}")
        print(f"Average items per site: {total_items/len(successful):.1f}")

    if failed:
        print(f"\nFailed sites:")
        for f in failed:
            print(f"  {f['ticker']}: {f['error']}")

if __name__ == "__main__":
    asyncio.run(main())