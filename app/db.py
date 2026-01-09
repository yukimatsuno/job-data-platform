import os
from dotenv import load_dotenv
from pymongo import MongoClient

# .env を読み込む
load_dotenv()

# 環境変数を取得
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "job_data_platform")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "herp")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set")

# MongoDB に接続
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
