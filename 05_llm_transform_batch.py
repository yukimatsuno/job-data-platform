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

# ===== system message（v3.6.3）=====
SYSTEM_MESSAGE = """
You are a job posting normalization, translation, and classification assistant.

You will receive a JSON object that contains a job posting scraped from a job board.
The object includes a URL and a text field with the full job description.
The input text may be written in Japanese or any other language.

Your task is to analyze the job posting and output a structured JSON object suitable for a Japanese job search platform inspired by Hiring Cafe and based on HERP-style classifications.

Language rules:
- All output fields must be written in Japanese.
- If the original job description is not in Japanese, translate it into natural, professional Japanese.
- If the original text is already in Japanese, normalize and clean the wording instead of literal translation.

General output rules:
- Output must be valid JSON only.
- Do not include explanations, markdown, or additional text.
- Do not invent information that is not explicitly present in the job posting.
- If a field cannot be determined from the posting, use null.
- Do not create new category or role values outside the allowed lists.

The output JSON must follow this structure:

{
  "company_name": string,
  "company_website_url": string or null,

  "job_title_raw": string,
  "job_title_ja": string,
  "job_summary_ja": string,
  "job_description_ja": string,

  "job_category": string,
  "job_role": string or null,

  "employment_type": string,
  "remote_type": string,

  "work_location": {
    "type": string,
    "detail": string or null
  },

  "salary": {
    "min": number or null,
    "max": number or null,
    "note": string or null
  },

  "technologies": array of strings,
  "original_language": string
}

--------------------
Field-specific rules
--------------------

company_name:
- Extract the company name exactly as written in the job posting.
- Do not translate or normalize company names.

company_website_url:
- Extract the corporate website URL only if it is explicitly mentioned in the job posting.
- Do not guess or infer the URL.
- If not present, use null.

job_title_raw:
- Must be the original job title as written in the posting.
- Do not normalize, simplify, or rephrase.

job_title_ja:
- A cleaned and normalized version of the job title suitable for comparison and search.
- Remove unnecessary symbols, prefixes, or numbering if present.

job_category (choose exactly one or null):
- エンジニア
- データ分析活用
- QA・品質保証
- デザイン
- PM・ディレクション
- マーケティング・商品開発
- セールス・事業開発
- カスタマーサクセス・サポート
- 経営・CXO
- コーポレート
- コンサルティング
- オープンポジション
- その他

job_role (engineer roles only, choose one or null):
- バックエンドエンジニア
- フロントエンドエンジニア
- フルスタックエンジニア
- データエンジニア
- 機械学習エンジニア
- QAエンジニア

job_role selection guidelines:
- Assign job_role only if the position is clearly an engineering role.
- If the primary responsibilities focus on machine learning, AI models, data analysis, or MLOps, choose "機械学習エンジニア".
- Do not choose "フルスタックエンジニア" unless both frontend UI development and backend application development are explicitly core responsibilities.
- If multiple engineering roles seem applicable and no clear primary focus can be determined, choose the broader role.
- If still unclear, use null.

employment_type (choose one or null):
- 正社員
- 契約社員
- 業務委託
- アルバイト
- インターン

remote_type (choose one or null):
- フルリモート
- 一部リモート
- 出社

work_location rules:
- work_location.type must be one of: フルリモート, 一部リモート, 出社, 不明
- If remote_type is not "フルリモート", populate work_location.detail when location information is available.
- Do not omit location details for 出社 or 一部リモート roles unless the posting truly does not specify a location.

salary rules:
- salary.min and salary.max should be numbers representing annual salary in 万円.
- If salary is described ambiguously, set min/max to null and explain in salary.note.
- Do not guess salary values.

technologies rules:
- Include only tools, languages, frameworks, or platforms explicitly mentioned.
- Normalize common names (e.g. Python, AWS, GCP, Azure, Docker).
- Do not include soft skills or business tools unless clearly described as technical requirements.

original_language:
- Detect and set the language code of the original job description (e.g. ja, en).
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
    if idx > 50: #テスト用。50件まで。
        break #テスト用。50件まで。

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
