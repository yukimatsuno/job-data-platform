import requests
from bs4 import BeautifulSoup
import time
import re
import pandas as pd

# Green Japanの求人リストページを巡回し、全てのユニークなcompany IDを抽出してCSVに保存するスクリプト

base_url = "https://www.green-japan.com/area/{}/01?page={}"
pref_ids = list(range(1, 48)) + [98, 99]
headers = {
    "User-Agent": "Mozilla/5.0"
}

def has_next_page(soup):
    next_link = soup.select_one(".pagination a[rel='next']")
    return next_link is not None

def extract_company_ids_from_page(url):
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch: {url}")
        return set()
    soup = BeautifulSoup(res.text, "html.parser")
    ids = set()
    for a in soup.select('a.card-info'):
        href = a.get('href')
        if href:
            m = re.match(r"/company/(\d+)/job/", href)
            if m:
                ids.add(m.group(1))
    return ids

if __name__ == "__main__":
    all_company_ids = set()
    for pref_id in pref_ids:
        print(f"--- Scraping prefecture ID: {pref_id} ---")
        page = 1
        while True:
            url = base_url.format(pref_id, page)
            print(f"Fetching: {url}")
            ids = extract_company_ids_from_page(url)
            print(f"  Found {len(ids)} company IDs on this page.")
            all_company_ids.update(ids)
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                print(f"  Failed to fetch page {page} for prefecture {pref_id}.")
                break
            soup = BeautifulSoup(res.text, "html.parser")
            if not has_next_page(soup):
                print(f"  No more pages for prefecture {pref_id}.")
                break
            page += 1
            time.sleep(1)

    print("\n--- Scraping complete ---")
    print(f"Total unique company IDs: {len(all_company_ids)}")

    # すべての company_id をCSVファイルに保存
    df = pd.DataFrame({'company_id': sorted(all_company_ids, key=int)})
    df.to_csv('12_green_company_ids.csv', index=False)
    print("All unique company IDs written to green_company_ids.csv")
