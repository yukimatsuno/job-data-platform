# db.py
# Database connection utilities (template)

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

if not all([MONGO_URI, DB_NAME, COLLECTION_NAME]):
    raise RuntimeError("MongoDB environment variables are not properly set")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Example usage:
# doc = collection.find_one({"url": "https://example.com"})
