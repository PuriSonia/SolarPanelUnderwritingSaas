from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from ..database import get_db
from ..models import GenerationData, GridConsumption, SolarSystem, Site
from ..deps import require_role
from ..audit import log_event

router = APIRouter(prefix="/upload", tags=["Uploads"])

@router.post("/generation/{solar_system_id}")
async def upload_generation(
    solar_system_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "manager"))
):
    system = db.query(SolarSystem).filter(SolarSystem.id == solar_system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Solar system not found")

    site = db.query(Site).filter(Site.id == system.site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=403, detail="Forbidden")

    df = pd.read_csv(file.file)
    inserted = 0
    for _, row in df.iterrows():
        month = str(row["month"])
        kwh = float(row["generation_kwh"])
        obj = db.query(GenerationData).filter(
            GenerationData.solar_system_id == solar_system_id,
            GenerationData.month == month
        ).first()
        if obj:
            obj.generation_kwh = kwh
        else:
            db.add(GenerationData(solar_system_id=solar_system_id, month=month, generation_kwh=kwh))
        inserted += 1

    db.commit()
    log_event(db, user=user, org_id=user.org_id, action="upload.generation", entity="SolarSystem", entity_id=str(solar_system_id), metadata={"rows": inserted})
    return {"message": "Generation data upserted", "rows": inserted}

@router.post("/grid/{site_id}")
async def upload_grid_consumption(
    site_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "manager"))
):
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    df = pd.read_csv(file.file)
    inserted = 0
    for _, row in df.iterrows():
        month = str(row["month"])
        kwh = float(row["grid_kwh"])
        obj = db.query(GridConsumption).filter(
            GridConsumption.site_id == site_id,
            GridConsumption.month == month
        ).first()
        if obj:
            obj.grid_kwh = kwh
        else:
            db.add(GridConsumption(site_id=site_id, month=month, grid_kwh=kwh))
        inserted += 1

    db.commit()
    log_event(db, user=user, org_id=user.org_id, action="upload.grid", entity="Site", entity_id=str(site_id), metadata={"rows": inserted})
    return {"message": "Grid consumption upserted", "rows": inserted}
