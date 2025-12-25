import pandas as pd

df = pd.read_csv('herp_companies_json_all.csv')
if 'companySlug' not in df.columns:
    print('companySlug column not found!')
else:
    unique_slugs = df['companySlug'].dropna().unique()
    print(f"Unique companySlug count: {len(unique_slugs)}")
    
    # すべての companySlug をCSVファイルに保存
    pd.DataFrame({'companySlug': unique_slugs}).to_csv('companyslugs.csv', index=False)
    print("All unique companySlugs written to companyslugs.csv")
