import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import JobCreate, JobUpdate, JobOut, Status

app = FastAPI(title="Production Kanban API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Kanban API running"}


# Utility to map Mongo doc to JobOut

def map_job(doc) -> JobOut:
    return JobOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        assigned_to=doc.get("assigned_to"),
        avatar_url=doc.get("avatar_url"),
        due_date=doc.get("due_date"),
        priority=doc.get("priority"),
        status=doc.get("status"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


@app.get("/api/jobs", response_model=List[JobOut])
async def list_jobs(status: Optional[Status] = None, q: Optional[str] = None):
    filter_dict = {}
    if status:
        filter_dict["status"] = status.value
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    docs = get_documents("job", filter_dict)
    # ensure order is stable by created_at
    docs = sorted(docs, key=lambda d: d.get("created_at") or datetime.min)
    return [map_job(d) for d in docs]


@app.post("/api/jobs", response_model=JobOut)
async def create_job(payload: JobCreate):
    data = payload.model_dump()
    inserted_id = create_document("job", data)
    doc = db["job"].find_one({"_id": ObjectId(inserted_id)})
    return map_job(doc)


@app.patch("/api/jobs/{job_id}", response_model=JobOut)
async def update_job(job_id: str, payload: JobUpdate):
    try:
        oid = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")

    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not update:
        doc = db["job"].find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Job not found")
        return map_job(doc)

    update["updated_at"] = datetime.utcnow()
    res = db["job"].find_one_and_update({"_id": oid}, {"$set": update}, return_document=True)
    doc = db["job"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return map_job(doc)


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    try:
        oid = ObjectId(job_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job id")
    res = db["job"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True}


@app.get("/test")
async def test_database():
    response = {
        "backend": "✅ Running",
    }
    try:
        _ = db.list_collection_names()
        response["database"] = "✅ Connected"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
