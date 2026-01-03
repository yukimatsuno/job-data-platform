import os
import json
import time
from openai import AzureOpenAI

# ===== Azure Foundry 設定 =====
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version="2024-07-01-preview"
)

DEPLOYMENT_NAME = "arpitja-gpt-4o-mini"

# ===== system message（v2）=====
SYSTEM_MESSAGE = """
You are a data transformation and classification assistant.
You will receive a JSON object that contains a job posting scraped from a job website.
The input text may be written in Japanese or English.

Output rules:
- Output must be valid JSON only.
- Do not include explanations or markdown.
- Translate all content into natural English.
- If a field cannot be determined, use null.

Output format:
{
  "en_job_title": string,
  "en_description": string,
  "job_department": string,
  "job_role": string,
  "technologies": array of strings
}
"""

INPUT_FILE = "04_job_texts.json"
OUTPUT_FILE = "05_llm_outputs.jsonl"
ERROR_FILE = "05_llm_errors.jsonl"

# ===== 入力読み込み =====
with open(INPUT_FILE, encoding="utf-8") as f:
    jobs = json.load(f)

total = len(jobs)
print(f"Total jobs: {total}")

# ===== 既に処理済みURLを読み込む（再開対応）=====
processed_urls = set()
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                processed_urls.add(obj.get("url"))
            except Exception:
                pass

# ===== メインループ =====
for idx, job in enumerate(jobs, 1):
    if idx >= 3: #テスト用。3件まで。
        break

    url = job.get("url")

    if url in processed_urls:
        print(f"[{idx}/{total}] SKIP: {url}")
        continue

    print(f"[{idx}/{total}] Processing: {url}")

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": json.dumps(job, ensure_ascii=False)}
            ],
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)
        result["url"] = url  # 元URLを保持

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            out.write(json.dumps(result, ensure_ascii=False) + "\n")

    except Exception as e:
        with open(ERROR_FILE, "a", encoding="utf-8") as err:
            err.write(json.dumps({
                "url": url,
                "error": str(e)
            }, ensure_ascii=False) + "\n")

    time.sleep(1)
