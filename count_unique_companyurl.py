import pandas as pd

df = pd.read_csv('herp_companies_json_all.csv')
if 'companyUrl' not in df.columns:
    print('companyUrl column not found!')
else:
    unique_urls = df['companySlug'].dropna().unique()
    print(f"Unique companySlug count: {len(unique_urls)}")
    print("Sample URLs:")
    print(unique_urls[:10])
