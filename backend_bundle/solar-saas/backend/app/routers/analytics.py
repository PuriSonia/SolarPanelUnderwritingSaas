from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import GenerationData, SolarSystem, Site, GridConsumption
from ..deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/site/{site_id}/monthly-generation")
def monthly_generation(site_id: int, year: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    systems = db.query(SolarSystem).filter(SolarSystem.site_id == site.id).all()

    out = {m: 0.0 for m in months}
    for system in systems:
        rows = db.query(GenerationData.month, func.sum(GenerationData.generation_kwh)).filter(
            GenerationData.solar_system_id == system.id,
            GenerationData.month.in_(months)
        ).group_by(GenerationData.month).all()
        for month, total in rows:
            out[month] += float(total or 0)

    return {"site_id": site_id, "year": year, "series": [{"month": k, "generation_kwh": v} for k, v in sorted(out.items())]}

@router.get("/site/{site_id}/monthly-grid")
def monthly_grid(site_id: int, year: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    out = {m: 0.0 for m in months}
    rows = db.query(GridConsumption.month, func.sum(GridConsumption.grid_kwh)).filter(
        GridConsumption.site_id == site_id,
        GridConsumption.month.in_(months)
    ).group_by(GridConsumption.month).all()
    for month, total in rows:
        out[month] += float(total or 0)

    return {"site_id": site_id, "year": year, "series": [{"month": k, "grid_kwh": v} for k, v in sorted(out.items())]}
