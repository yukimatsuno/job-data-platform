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
