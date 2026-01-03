import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# -----------------------------
# 環境変数の読み込み（.env）
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# 環境変数が未設定の場合は即エラーにする
if not all([MONGO_URI, DB_NAME, COLLECTION_NAME]):
    raise RuntimeError("MongoDB environment variables are not properly set")

# -----------------------------
# MongoDB 接続確認
# -----------------------------
client = MongoClient(MONGO_URI)

# 実際に接続できるかを明示的に確認
client.admin.command("ping")
print("MongoDB connected")

# 使用する DB / Collection
collection = client[DB_NAME][COLLECTION_NAME]

# -----------------------------
# JSONL を読み込み、MongoDB に upsert
# -----------------------------
with open("05_llm_outputs.jsonl", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        try:
            # 1行 = 1求人データ（JSON）
            doc = json.loads(line)

            # URL をキーにして upsert（再実行に強い）
            collection.update_one(
                {"url": doc.get("url")},
                {"$set": doc},
                upsert=True
            )

        except Exception as e:
            # 壊れた行があっても処理は止めない
            print(f"Skip line {i}: {e}")

print("Import completed")
