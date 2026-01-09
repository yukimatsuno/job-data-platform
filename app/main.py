from fastapi import FastAPI
from app.db import collection

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI"}

@app.get("/job/sample")
def get_sample_job():
    """
    MongoDB から求人データを1件だけ取得して返す
    """
    doc = collection.find_one()

    if not doc:
        return {"message": "No data found"}

    # MongoDB の _id(ObjectId) は JSON にできないので文字列に変換
    doc["_id"] = str(doc["_id"])
    return doc

@app.get("/jobs")
def list_jobs(limit: int = 10):
    """
    求人一覧を返す（デフォルト10件）
    """
    cursor = collection.find().limit(limit)

    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    return results