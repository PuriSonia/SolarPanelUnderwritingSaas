from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tariff, Site
from ..schemas import TariffUpsert
from ..deps import require_role
from ..audit import log_event

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])

@router.post("/upsert")
def upsert_tariff(data: TariffUpsert, db: Session = Depends(get_db), user=Depends(require_role("admin", "manager"))):
    site = db.query(Site).filter(Site.id == data.site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    obj = db.query(Tariff).filter(Tariff.site_id == data.site_id).first()
    if obj:
        obj.rate_per_kwh = data.rate_per_kwh
        obj.tariff_type = data.tariff_type
        obj.demand_charge = data.demand_charge
    else:
        obj = Tariff(site_id=data.site_id, rate_per_kwh=data.rate_per_kwh, tariff_type=data.tariff_type, demand_charge=data.demand_charge)
        db.add(obj)

    db.commit()
    log_event(db, user=user, org_id=user.org_id, action="tariff.upsert", entity="Site", entity_id=str(data.site_id), metadata={"rate": data.rate_per_kwh})
    return {"ok": True}
