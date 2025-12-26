import requests
import pandas as pd
import time

API_BASE = "https://herp.careers/careers/api/v1/jobs"
SORTS = [
    None,  # default (新着順)
    "employees_desc",
    "employees_asc",
    "members_voice_desc",
]

all_companies = []

for sort in SORTS:
    for page in range(1, 51):
        params = {"page": page}
        if sort:
            params["sort"] = sort
        print(f"Fetching: {API_BASE} with params {params}")
        resp = requests.get(API_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        companies = data.get("companies")
        if not isinstance(companies, list):
            print(f"Warning: 'companies' not found or not a list on page {page}, sort {sort}.")
            print(data)
            break  # ページが尽きたら次のソートへ
        if not companies:
            print(f"No companies found on page {page}, sort {sort}. Stopping this sort.")
            break
        for company in companies:
            company["_sort"] = sort or "default"
            company["_page"] = page
            all_companies.append(company)
        print(f"  Got {len(companies)} companies for sort={sort}, page={page}")
        time.sleep(0.5)

# Find all unique keys
all_keys = set()
for company in all_companies:
    all_keys.update(company.keys())

# Build rows with all keys
rows = []
for company in all_companies:
    row = {k: company.get(k, None) for k in all_keys}
    rows.append(row)

# Save to CSV
out_csv = "herp_companies_json_all.csv"
df = pd.DataFrame(rows)
df.to_csv(out_csv, index=False)
print(f"Saved {len(df)} rows to {out_csv}")
