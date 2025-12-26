import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# Load all company slugs
slugs = pd.read_csv('companyslugs.csv')['companySlug'].dropna().unique()

results = []

for slug in slugs:
    url = f'https://herp.careers/careers/companies/{slug}/jobs'
    print(f'Scraping {url}')
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 求人リンクのみ抽出
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(f'/careers/companies/{slug}/jobs/'):
                title = a.get_text(strip=True)
                link = 'https://herp.careers' + href
                results.append({'companySlug': slug, 'jobTitle': title, 'jobLink': link})
    except Exception as e:
        print(f'  Failed to scrape {url}: {e}')
    time.sleep(0.5)

# Save results
pd.DataFrame(results).to_csv('company_jobs.csv', index=False)
print(f'Saved {len(results)} job entries to company_jobs.csv')
