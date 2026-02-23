from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Site
from ..deps import require_role
from ..tasks import generate_site_report

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/site/{site_id}/year/{year}")
def request_site_report(site_id: int, year: str, region: str = "default", db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    task = generate_site_report.delay(user.org_id, site_id, year, region)
    return {"task_id": task.id}

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    from celery.result import AsyncResult
    res = AsyncResult(task_id)
    payload = {"task_id": task_id, "state": res.state}
    if res.successful():
        payload["result"] = res.result
    elif res.failed():
        payload["error"] = str(res.result)
    return payload
