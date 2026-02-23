from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Site, SolarSystem, GenerationData, GridConsumption, Tariff
from ..deps import get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("/summary")
def portfolio_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    sites = db.query(Site).filter(Site.org_id == user.org_id).all()

    total_generation = 0.0
    total_grid = 0.0
    total_savings = 0.0

    for site in sites:
        systems = db.query(SolarSystem).filter(SolarSystem.site_id == site.id).all()
        tariff = db.query(Tariff).filter(Tariff.site_id == site.id).first()
        rate = tariff.rate_per_kwh if tariff else 0.0

        for system in systems:
            gen = db.query(func.sum(GenerationData.generation_kwh)).filter(GenerationData.solar_system_id == system.id).scalar() or 0.0
            total_generation += float(gen)
            total_savings += float(gen) * rate

        grid = db.query(func.sum(GridConsumption.grid_kwh)).filter(GridConsumption.site_id == site.id).scalar() or 0.0
        total_grid += float(grid)

    return {"total_sites": len(sites), "total_generation_kwh": total_generation, "total_grid_kwh": total_grid, "estimated_total_savings": total_savings}
