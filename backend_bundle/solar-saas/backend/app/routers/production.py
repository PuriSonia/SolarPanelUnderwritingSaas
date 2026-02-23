from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProductionData, Site
from ..deps import require_role, get_current_user
from ..audit import log_event

router = APIRouter(prefix="/production", tags=["Production Data"])

@router.post("/site/{site_id}/year/{year}")
def upsert(site_id: int, year: int, production_units: float, db: Session = Depends(get_db), user=Depends(require_role("admin","manager"))):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    obj = db.query(ProductionData).filter(ProductionData.site_id == site_id, ProductionData.year == year).first()
    if obj:
        obj.production_units = production_units
    else:
        obj = ProductionData(site_id=site_id, year=year, production_units=production_units)
        db.add(obj)
    db.commit()
    log_event(db, user=user, org_id=user.org_id, action="production.upsert", entity="Site", entity_id=str(site_id), metadata={"year": year, "units": production_units})
    return {"ok": True}

@router.get("/site/{site_id}/year/{year}")
def get(site_id: int, year: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    obj = db.query(ProductionData).filter(ProductionData.site_id == site_id, ProductionData.year == year).first()
    return {"site_id": site_id, "year": year, "production_units": obj.production_units if obj else None}
