from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import EmissionFactor
from ..schemas import EmissionFactorCreate, EmissionFactorApprove
from ..deps import require_role, get_current_user
from ..audit import log_event

router = APIRouter(prefix="/emission-factors", tags=["Emission Factors"])

@router.post("/")
def create_ef(data: EmissionFactorCreate, db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    max_v = db.query(func.max(EmissionFactor.version)).filter(EmissionFactor.region == data.region).scalar() or 0
    ef = EmissionFactor(
        region=data.region,
        factor_t_per_kwh=data.factor_t_per_kwh,
        source=data.source,
        version=int(max_v) + 1,
        status="draft",
        effective_from=date.fromisoformat(data.effective_from) if data.effective_from else None,
        effective_to=date.fromisoformat(data.effective_to) if data.effective_to else None,
    )
    db.add(ef)
    db.commit()
    db.refresh(ef)
    log_event(db, user=user, org_id=user.org_id, action="ef.create", entity="EmissionFactor", entity_id=str(ef.id), metadata={"region": ef.region, "version": ef.version})
    return ef

@router.post("/approve")
def approve_ef(data: EmissionFactorApprove, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    ef = db.query(EmissionFactor).filter(EmissionFactor.id == data.id).first()
    if not ef:
        raise HTTPException(status_code=404, detail="Emission factor not found")

    ef.status = "approved"
    ef.approved_by_user_id = user.id
    ef.approved_at = datetime.utcnow()
    db.commit()

    log_event(db, user=user, org_id=user.org_id, action="ef.approve", entity="EmissionFactor", entity_id=str(ef.id), metadata={"region": ef.region, "version": ef.version})
    return {"ok": True, "id": ef.id}

@router.get("/")
def list_efs(region: str | None = None, status: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(EmissionFactor)
    if region:
        q = q.filter(EmissionFactor.region == region)
    if status:
        q = q.filter(EmissionFactor.status == status)
    return q.order_by(EmissionFactor.region.asc(), EmissionFactor.version.desc()).all()
