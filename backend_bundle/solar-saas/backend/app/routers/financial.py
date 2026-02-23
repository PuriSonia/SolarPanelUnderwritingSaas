from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import GenerationData, Tariff, SolarSystem, Site
from ..deps import get_current_user
from ..audit import log_event

router = APIRouter(prefix="/financial", tags=["Financial"])

@router.get("/site/{site_id}/summary")
def site_financial_summary(site_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    tariff = db.query(Tariff).filter(Tariff.site_id == site_id).first()
    rate = tariff.rate_per_kwh if tariff else 0.0

    systems = db.query(SolarSystem).filter(SolarSystem.site_id == site_id).all()
    total_generation = 0.0
    for system in systems:
        gen = db.query(func.sum(GenerationData.generation_kwh)).filter(
            GenerationData.solar_system_id == system.id
        ).scalar() or 0.0
        total_generation += float(gen)

    savings = total_generation * rate
    log_event(db, user=user, org_id=user.org_id, action="financial.view", entity="Site", entity_id=str(site_id))
    return {"site_id": site_id, "total_generation_kwh": total_generation, "tariff_rate_per_kwh": rate, "estimated_savings": savings}
