import httpx, time

def test():
    url='https://investors.3m.com/financials/quarterly-results/default.aspx'
    t0=time.time()
    with httpx.Client(timeout=180) as client:
        r=client.post('http://127.0.0.1:8001/scrape', json={'source_url':url})
    print('status', r.status_code, 'time', round(time.time()-t0,2))
    try:
        print(r.json())
    except Exception as e:
        print('json parse error', e)

test()
