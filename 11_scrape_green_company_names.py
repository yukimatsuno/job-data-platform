import requests
from bs4 import BeautifulSoup
import time

# 例: リストページのURL（都道府県IDやページ番号は適宜変更）
urls = [
    "https://www.green-japan.com/area/99/05",
    # 他のURLもここに追加可能
]

headers = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_company_names(url):
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch: {url}")
        return []
    soup = BeautifulSoup(res.text, "html.parser")
    company_names = [h3.text.strip() for h3 in soup.select("h3.card-info__detail-area__box__title")]
    return company_names

if __name__ == "__main__":
    for url in urls:
        names = scrape_company_names(url)
        for name in names:
            print(name)
        time.sleep(1)  # サーバー負荷軽減
