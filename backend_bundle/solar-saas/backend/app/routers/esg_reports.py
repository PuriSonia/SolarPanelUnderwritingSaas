from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..audit import log_event
from ..services.esg_engine import compute_site_year, compute_org_year, compute_yoy_delta

router = APIRouter(prefix="/esg-reports", tags=["ESG Reports"])

@router.get("/site/{site_id}/annual")
def site_annual(site_id: int, year: int, region: str = "default", db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        res = compute_site_year(db, org_id=user.org_id, site_id=site_id, year=year, region=region)
    except ValueError:
        raise HTTPException(status_code=404, detail="Site not found")
    log_event(db, user=user, org_id=user.org_id, action="esg.site.annual", entity="Site", entity_id=str(site_id), metadata={"year": year, "region": region})
    return res.__dict__

@router.get("/org/annual")
def org_annual(year: int, region: str = "default", db: Session = Depends(get_db), user=Depends(get_current_user)):
    res = compute_org_year(db, org_id=user.org_id, year=year, region=region)
    log_event(db, user=user, org_id=user.org_id, action="esg.org.annual", metadata={"year": year, "region": region})
    return res.__dict__

@router.get("/site/{site_id}/scorecard")
def site_scorecard(site_id: int, year: int, region: str = "default", db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        annual = compute_site_year(db, org_id=user.org_id, site_id=site_id, year=year, region=region)
    except ValueError:
        raise HTTPException(status_code=404, detail="Site not found")
    yoy = compute_yoy_delta(db, org_id=user.org_id, site_id=site_id, year=year, region=region)
    payload = {
        "year": year,
        "site_id": site_id,
        "renewable_percentage": annual.renewable_percentage,
        "energy_intensity": annual.energy_intensity,
        "solar_avoided_tco2e": annual.avoided_emissions_tco2e,
        "net_scope2_tco2e": annual.net_scope2_tco2e,
        "yoy": yoy,
        "methodology": annual.methodology,
        "emission_factor_t_per_kwh": annual.emission_factor_t_per_kwh,
        "emission_factor_version": annual.emission_factor_version,
        "emission_factor_source": annual.emission_factor_source,
    }
    log_event(db, user=user, org_id=user.org_id, action="esg.site.scorecard", entity="Site", entity_id=str(site_id), metadata={"year": year, "region": region})
    return payload
