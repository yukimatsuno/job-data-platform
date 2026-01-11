
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from app.db import collection
from fastapi.staticfiles import StaticFiles
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI"}



@app.get("/", response_class=HTMLResponse)
def show_jobs(
    request: Request,
    limit: int = 50,
    q: Optional[str] = None,
    job_category: Optional[str] = None,
    employment_type: Optional[str] = None,
    remote_type: Optional[str] = None,
    work_location: Optional[str] = None,
    salary_min: Optional[str] = None,
    salary_max: Optional[str] = None,
    employee_count: Optional[str] = None,
):
    query = {}
    and_conditions = []
    if q:
        and_conditions.append({
            "$or": [
                {"job_title_raw": {"$regex": q, "$options": "i"}},
                {"company_name": {"$regex": q, "$options": "i"}},
                {"job_category": {"$regex": q, "$options": "i"}},
                {"job_role": {"$regex": q, "$options": "i"}}
            ]
        })
    if job_category:
        and_conditions.append({"job_category": job_category})
    if employment_type:
        and_conditions.append({"employment_type": employment_type})
    if remote_type:
        if remote_type == "未設定":
            and_conditions.append({
                "$or": [
                    {"remote_type": {"$in": [None, "", "未設定"]}},
                    {"remote_type": None},
                    {"remote_type": {"$exists": False}}
                ]
            })
        else:
            and_conditions.append({"remote_type": remote_type})
    if work_location:
        # work_location.type or work_location.detail どちらかに一致
        and_conditions.append({
            "$or": [
                {"work_location.type": work_location},
                {"work_location.detail": {"$regex": work_location, "$options": "i"}}
            ]
        })
    if salary_min and salary_min != "":
        try:
            salary_min_int = int(salary_min)
            and_conditions.append({"salary.min": {"$gte": salary_min_int}})
        except Exception:
            pass
    if salary_max and salary_max != "":
        try:
            salary_max_int = int(salary_max)
            and_conditions.append({"salary.max": {"$lte": salary_max_int}})
        except Exception:
            pass
    if employee_count:
        # employee_count is like '100-299', '5000-', etc.
        if '-' in employee_count:
            parts = employee_count.split('-')
            if parts[1] == '':
                # 5000- (5000人以上)
                and_conditions.append({"employee_count": {"$gte": int(parts[0])}})
            else:
                and_conditions.append({"employee_count": {"$gte": int(parts[0]), "$lte": int(parts[1])}})
    if and_conditions:
        query = {"$and": and_conditions}
    cursor = collection.find(query).sort("_id", -1).limit(limit)
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
