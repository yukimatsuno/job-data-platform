from fastapi import FastAPI
from app.db import collection
from bson import ObjectId
from fastapi import HTTPException

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI"}

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

@app.get("/jobs/{job_id}")
def get_job_detail(job_id: str):
    """
    MongoDB の _id を使って、求人を1件取得する
    """

    # ① job_id が MongoDB の形式かチェック
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job id")

    # ② MongoDB から1件取得
    doc = collection.find_one({"_id": ObjectId(job_id)})

    # ③ 見つからなかった場合
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")

    # ④ ObjectId を文字列に変換
    doc["_id"] = str(doc["_id"])

    return doc
