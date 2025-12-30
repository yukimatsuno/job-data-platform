import csv
import time
import traceback
from pathlib import Path

import requests
from bs4 import BeautifulSoup

def extract_text_from_class(url: str) -> str:
    """
    指定したURLのページから、対象要素内のテキスト内容をすべて抽出します。
    引数:
        url (str): 対象となるWebページのURL
    戻り値:
        str: 抽出したテキスト内容。対象要素が見つからない場合は空文字列を返します。
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    ids = ["job-overview", "qualifications", "compensation", "company-overview"]
    texts = []
    for id_name in ids:
        elem = soup.find(id=id_name)
        if not elem:
            continue
        
        # job-match-analysisを含む子要素を除外
        job_match = elem.find(id="job-match-analysis")
        if job_match:
            job_match.extract()

        # company-overview内の特定divを除外
        if id_name == "company-overview":
            exclude_div = elem.find('div', class_="flex flex-col gap-4")
            if exclude_div:
                exclude_div.extract()

        texts.append(elem.get_text(separator='\n', strip=True))

    # 更新日時のテキストを抽出
    update_elems = soup.find_all('p', class_="scroll-m-20 text-sm text-pretty text-gray-600")
    for elem in update_elems:
        texts.append(elem.get_text(strip=True))
    if texts:
        return '\n\n'.join(texts)
    return ""

def atomic_write_json(path: str, data):
    """
    JSONデータを一時ファイル経由で安全に書き込み、途中停止でもファイルが壊れないように保存
    """
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def append_jsonl(path: str, obj: dict):
    """1行ごとに1つのJSONオブジェクトを追記"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def process_job_cards(input_csv: str, output_json: str, delay: float = 1.0, max_rows: int = None):
    """
    求人カードのURLをバッチ処理し、各バッチごとに結果を保存し、エラーも記録。
    引数:
        input_csv (str): 求人URL一覧のCSV
        output_json (str): 抽出した本文を保存するJSON
        delay (float): URL間の待ち時間
        max_rows (int): 処理件数制限（サンプル用）
    """
    import os
    import json
    results = []
    seen_urls = set()
    
    # 既にアウトプットが存在する場合、続きから再開
    if os.path.exists(output_json):
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                results = json.load(f)
            seen_urls = {r.get('url') for r in results if r.get('url')}
            print(f"Resuming: loaded {len(results)} results")
        except Exception:
            print("Failed to load existing results, starting fresh.")
            results = []
            seen_urls = set()
    
    errors_jsonl = "04_scrape_errors.jsonl"

    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        url = row.get("jobLink") or row.get("url")
        if not url:
            continue

        if url in seen_urls:
            print(f"[{idx}/{total}] SKIP (already saved): {url}")
            continue

        print(f"[{idx}/{total}] scraping: {url}")

        try:
            text = extract_text_from_class(url)
            results.append({"url": url, "text": text})
            seen_urls.add(url)

            # 毎回保存
            atomic_write_json(output_json, results)

        except Exception as e:
            append_jsonl(errors_jsonl, {
                "url": url,
                "error": str(e),
                "trace": traceback.format_exc(),
            })

        time.sleep(delay)

if __name__ == "__main__":
    process_all = False  # True：全件、False：サンプル
    import json
    import csv
    input_path = '03_company_jobs.csv'

    if process_all:
        output_path = '04_job_texts.json'
        max_rows = None # 制限なし
    else:
        output_path = '04_job_texts_sample.json'
        max_rows = 3 # 先頭3件のみ
    process_job_cards(
        input_csv=input_path, 
        output_json=output_path, 
        delay=1.0,
        max_rows=max_rows
        )