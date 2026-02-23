from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Site
from ..schemas import SiteCreate
from ..deps import get_current_user, require_role
from ..audit import log_event

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.post("/")
def create_site(data: SiteCreate, db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    site = Site(name=data.name, location=data.location, org_id=user.org_id)
    db.add(site)
    db.commit()
    db.refresh(site)
    log_event(db, user=user, org_id=user.org_id, action="site.create", entity="Site", entity_id=str(site.id), metadata={"name": site.name})
    return site

@router.get("/")
def list_sites(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Site).filter(Site.org_id == user.org_id).order_by(Site.id.desc()).all()
