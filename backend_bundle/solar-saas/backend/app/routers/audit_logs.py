from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AuditLog
from ..deps import require_role

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/")
def list_audit(limit: int = 100, db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    return (
        db.query(AuditLog)
        .filter(AuditLog.org_id == user.org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )
