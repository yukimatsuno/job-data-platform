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

def scrape_company_links(url):
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch: {url}")
        return []
    soup = BeautifulSoup(res.text, "html.parser")
    # 会社名のaタグ（求人詳細ページへのリンク）を抽出
    links = []
    for a in soup.select('a.card-info'):
        href = a.get('href')
        if href:
            full_url = "https://www.green-japan.com" + href
            links.append(full_url)
    return links

if __name__ == "__main__":
    for url in urls:
        links = scrape_company_links(url)
        for link in links:
            print(link)
        time.sleep(1)  # サーバー負荷軽減
