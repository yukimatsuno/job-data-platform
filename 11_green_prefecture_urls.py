
import requests
from bs4 import BeautifulSoup
import time

base_url = "https://www.green-japan.com/area/{}/01?page={}"
pref_ids = list(range(1, 48)) + [98, 99]

headers = {
    "User-Agent": "Mozilla/5.0"
}

def has_next_page(soup):
    # 「次へ」ボタンが存在するか判定
    next_link = soup.select_one(".pagination a[rel='next']")
    return next_link is not None

if __name__ == "__main__":
    for pref_id in pref_ids:
        page = 1
        while True:
            url = base_url.format(pref_id, page)
            print(url)
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            if not has_next_page(soup):
                break
            page += 1
            time.sleep(1)  # サーバー負荷軽減
