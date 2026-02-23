from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SolarSystem, Site
from ..schemas import SolarSystemCreate
from ..deps import get_current_user, require_role
from ..audit import log_event

router = APIRouter(prefix="/solar", tags=["Solar Systems"])

@router.post("/")
def create_solar_system(data: SolarSystemCreate, db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    site = db.query(Site).filter(Site.id == data.site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    system = SolarSystem(
        site_id=data.site_id,
        name=data.name,
        capacity_kw=data.capacity_kw,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    log_event(db, user=user, org_id=user.org_id, action="solar.create", entity="SolarSystem", entity_id=str(system.id), metadata={"site_id": data.site_id})
    return system

@router.get("/site/{site_id}")
def list_systems(site_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return db.query(SolarSystem).filter(SolarSystem.site_id == site_id).order_by(SolarSystem.id.desc()).all()
