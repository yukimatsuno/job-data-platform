import csv
import time
import traceback
from pathlib import Path

# --- extract_text_from_class 関数をこのファイル内に直接定義 ---
import requests
from bs4 import BeautifulSoup

def extract_text_from_class(url: str, class_name: str) -> str:
    """
    Extracts all text content from the first element with the given class name on the page at the specified URL.
    Args:
        url (str): The URL of the web page.
        class_name (str): The class name of the element to extract text from.
    Returns:
        str: The extracted text content, or an empty string if not found.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    ids = ["job-overview", "qualifications", "compensation", "company-overview"]
    texts = []
    for id_name in ids:
        elem = soup.find(id=id_name)
        if elem:
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
    # 追加で更新日時のテキストも抽出
    update_elems = soup.find_all('p', class_="scroll-m-20 text-sm text-pretty text-gray-600")
    for elem in update_elems:
        texts.append(elem.get_text(strip=True))
    if texts:
        return '\n\n'.join(texts)
    return ""

def process_job_cards(input_csv, output_csv, batch_size=100, delay=1):
    """
    Processes job card URLs in batches, saves results after each batch, and logs errors.
    Args:
        input_csv (str): Path to CSV file with a column 'url' containing job URLs.
        output_csv (str): Path to save results (CSV).
        batch_size (int): Number of URLs to process per batch.
        delay (int): Seconds to wait between requests.
    """
    # Track already processed URLs
    processed = set()
    if Path(output_csv).exists():
        with open(output_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.add(row['url'])

    results = []
    errors = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        total = 0
        for row in reader:
            # 03_company_jobs.csvの場合、URLは'jobLink'列
            url = row.get('jobLink') or row.get('url')
            if not url or url in processed:
                continue
            batch.append(url)
            total += 1
            if len(batch) == batch_size:
                for i, u in enumerate(batch):
                    print(f"スクレイピング中: {total - len(batch) + i + 1}件目 {u}")
                    try:
                        text = extract_text_from_class(u, None)
                        results.append({'url': u, 'text': text})
                    except Exception as e:
                        errors.append({'url': u, 'error': str(e), 'trace': traceback.format_exc()})
                    time.sleep(delay)
                # Save batch results
                with open(output_csv, 'a', newline='', encoding='utf-8') as out:
                    writer = csv.DictWriter(out, fieldnames=['url', 'text'])
                    if out.tell() == 0:
                        writer.writeheader()
                    writer.writerows(results)
                results.clear()
                batch.clear()
        # Process any remaining URLs
        for i, u in enumerate(batch):
            print(f"スクレイピング中: {total - len(batch) + i + 1}件目 {u}")
            try:
                text = extract_text_from_class(u, None)
                results.append({'url': u, 'text': text})
            except Exception as e:
                errors.append({'url': u, 'error': str(e), 'trace': traceback.format_exc()})
            time.sleep(delay)
    if results:
        with open(output_csv, 'a', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['url', 'text'])
            if out.tell() == 0:
                writer.writeheader()
            writer.writerows(results)
    # Save errors
    if errors:
        with open('scrape_errors.csv', 'a', newline='', encoding='utf-8') as err:
            writer = csv.DictWriter(err, fieldnames=['url', 'error', 'trace'])
            if err.tell() == 0:
                writer.writeheader()
            writer.writerows(errors)

if __name__ == "__main__":
    # Trueなら全件、Falseなら先頭3件のみ
    process_all = False  # ここをTrueにすると全件、Falseでサンプルのみ
    import json
    import csv
    input_path = '03_company_jobs.csv'
    if process_all:
        output_path = '05_job_texts.json'
        with open(input_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    else:
        output_path = '05_job_texts_sample.json'
        n = 3
        with open(input_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = [row for i, row in enumerate(reader) if i < n]
    def process_rows(rows, output_json):
        results = []
        errors = []
        total = len(rows)
        for idx, row in enumerate(rows):
            url = row.get('jobLink') or row.get('url')
            print(f"スクレイピング中: {total}件中{idx+1}件目 {url}")
            try:
                text = extract_text_from_class(url, None)
                results.append({'url': url, 'text': text})
            except Exception as e:
                import traceback
                errors.append({'url': url, 'error': str(e), 'trace': traceback.format_exc()})
            import time
            time.sleep(1)
        # Save results as JSON
        if results:
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump(results, out, ensure_ascii=False, indent=2)
        # Save errors
        if errors:
            with open('05_scrape_errors.json', 'a', encoding='utf-8') as err:
                json.dump(errors, err, ensure_ascii=False, indent=2)
    process_rows(rows, output_path)
