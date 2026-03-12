import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import uuid
from app.database import init_db, SessionLocal
from app.models import Request, AuditLog        # ← THIS WAS MISSING
from app.engine import DecisionEngine

app = FastAPI(title="Resilient Decision Platform")

# Load config
with open("config/workflows.json") as f:
    WORKFLOWS = json.load(f)
engine = DecisionEngine(WORKFLOWS)

init_db()

class SubmitRequest(BaseModel):
    request_id: str | None = None
    workflow_id: str
    data: dict

@app.post("/requests/")
async def submit_request(req: SubmitRequest):
    request_id = req.request_id or str(uuid.uuid4())
    
    db = SessionLocal()
    existing = db.query(Request).filter_by(id=request_id).first()
    if existing and existing.status != "pending":
        db.close()
        return {"request_id": request_id, "status": existing.status, "note": "Idempotent response - already processed"}
    
    if not existing:
        db.add(Request(id=request_id, workflow_id=req.workflow_id, data=req.data))
        db.commit()
    db.close()

    result = engine.run_workflow(request_id, req.workflow_id, req.data)
    return result

@app.get("/requests/{request_id}")
async def get_request(request_id: str):
    db = SessionLocal()
    req = db.query(Request).filter_by(id=request_id).first()
    if not req:
        db.close()
        raise HTTPException(status_code=404, detail="Request not found")
    
    logs = db.query(AuditLog).filter_by(request_id=request_id).all()
    db.close()
    
    # Convert to plain dict so it returns clean JSON
    audit_logs = [
        {
            "id": log.id,
            "stage": log.stage,
            "rule": log.rule,
            "result": log.result,
            "explanation": log.explanation,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in logs
    ]
    
    return {
        "request_id": request_id,
        "status": req.status,
        "audit_logs": audit_logs
    }

@app.get("/workflows")
async def list_workflows():
    return WORKFLOWS