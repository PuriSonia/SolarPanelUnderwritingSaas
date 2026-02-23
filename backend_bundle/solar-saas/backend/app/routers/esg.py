from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import GridConsumption, EmissionFactor, GenerationData, SolarSystem, Site
from ..deps import get_current_user
from ..audit import log_event

router = APIRouter(prefix="/esg", tags=["ESG"])

@router.get("/site/{site_id}/scope2")
def scope2(site_id: int, region: str = "default", db: Session = Depends(get_db), user=Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    ef = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.region == region, EmissionFactor.status == "approved")
        .order_by(EmissionFactor.version.desc())
        .first()
    )
    ef_val = ef.factor_t_per_kwh if ef else 0.0

    total_grid = db.query(func.sum(GridConsumption.grid_kwh)).filter(GridConsumption.site_id == site_id).scalar() or 0.0

    systems = db.query(SolarSystem).filter(SolarSystem.site_id == site_id).all()
    total_solar = 0.0
    for system in systems:
        gen = db.query(func.sum(GenerationData.generation_kwh)).filter(GenerationData.solar_system_id == system.id).scalar() or 0.0
        total_solar += float(gen)

    gross = float(total_grid) * ef_val
    avoided = float(total_solar) * ef_val
    net = gross - avoided

    log_event(db, user=user, org_id=user.org_id, action="esg.scope2.view", entity="Site", entity_id=str(site_id), metadata={"region": region})
    return {
        "region": region,
        "emission_factor_version": ef.version if ef else None,
        "emission_factor_t_per_kwh": ef_val,
        "gross_scope2_tco2e": gross,
        "avoided_by_solar_tco2e": avoided,
        "net_scope2_tco2e": net,
        "total_grid_kwh": float(total_grid),
        "total_solar_kwh": float(total_solar),
    }
