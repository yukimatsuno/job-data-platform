from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from app.db import collection
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI"}


@app.get("/", response_class=HTMLResponse)
def show_jobs(request: Request, limit: int = 10):
    cursor = collection.find().sort("_id", -1).limit(limit)
    jobs = []

    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        jobs.append(doc)

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "jobs": jobs},
    )


@app.get("/job/{job_id}", response_class=HTMLResponse)
def show_job_detail(request: Request, job_id: str):
    if not ObjectId.is_valid(job_id):
        return HTMLResponse("Invalid job id", status_code=400)

    doc = collection.find_one({"_id": ObjectId(job_id)})
    if not doc:
        return HTMLResponse("Job not found", status_code=404)

    doc["_id"] = str(doc["_id"])

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": doc},
    )
