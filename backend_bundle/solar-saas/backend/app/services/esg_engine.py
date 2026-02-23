from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Site, GridConsumption, SolarSystem, GenerationData, EmissionFactor, ProductionData

@dataclass
class ESGAnnualResult:
    year: int
    total_grid_kwh: float
    total_solar_kwh: float
    gross_scope2_tco2e: float
    avoided_emissions_tco2e: float
    net_scope2_tco2e: float
    renewable_percentage: float
    energy_intensity: Optional[float]
    methodology: str
    emission_factor_t_per_kwh: float
    emission_factor_version: Optional[int]
    emission_factor_source: Optional[str]

def _year_months(year: int):
    return [f"{year}-{m:02d}" for m in range(1, 13)]

def _get_approved_ef(db: Session, region: str, year: int):
    # Prefer the latest approved version for region. (Optionally you could filter by effective dates.)
    q = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.region == region, EmissionFactor.status == "approved")
        .order_by(EmissionFactor.version.desc())
    )
    return q.first()

def compute_site_year(db: Session, *, org_id: int, site_id: int, year: int, region: str = "default") -> ESGAnnualResult:
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == org_id).first()
    if not site:
        raise ValueError("site not found")

    months = _year_months(year)

    total_grid = db.query(func.sum(GridConsumption.grid_kwh)).filter(
        GridConsumption.site_id == site_id,
        GridConsumption.month.in_(months),
    ).scalar() or 0.0

    systems = db.query(SolarSystem).filter(SolarSystem.site_id == site_id).all()
    total_solar = 0.0
    for sys in systems:
        gen = db.query(func.sum(GenerationData.generation_kwh)).filter(
            GenerationData.solar_system_id == sys.id,
            GenerationData.month.in_(months),
        ).scalar() or 0.0
        total_solar += float(gen)

    ef = _get_approved_ef(db, region, year)
    ef_val = float(ef.factor_t_per_kwh) if ef else 0.0

    gross = float(total_grid) * ef_val
    avoided = float(total_solar) * ef_val
    net = gross - avoided
    denom = float(total_grid) + float(total_solar)
    renewable_pct = (float(total_solar) / denom * 100.0) if denom > 0 else 0.0

    # Energy intensity (BRSR-style) = total energy / production units (if provided)
    prod = db.query(ProductionData).filter(ProductionData.site_id == site_id, ProductionData.year == year).first()
    energy_intensity = None
    if prod and prod.production_units and prod.production_units > 0:
        energy_intensity = (float(total_grid) + float(total_solar)) / float(prod.production_units)

    return ESGAnnualResult(
        year=year,
        total_grid_kwh=float(total_grid),
        total_solar_kwh=float(total_solar),
        gross_scope2_tco2e=round(gross, 4),
        avoided_emissions_tco2e=round(avoided, 4),
        net_scope2_tco2e=round(net, 4),
        renewable_percentage=round(renewable_pct, 2),
        energy_intensity=round(energy_intensity, 6) if energy_intensity is not None else None,
        methodology="GHG Protocol Scope 2 (location-based)",
        emission_factor_t_per_kwh=ef_val,
        emission_factor_version=int(ef.version) if ef else None,
        emission_factor_source=ef.source if ef else None,
    )

def compute_org_year(db: Session, *, org_id: int, year: int, region: str = "default") -> ESGAnnualResult:
    sites = db.query(Site).filter(Site.org_id == org_id).all()
    total_grid = 0.0
    total_solar = 0.0
    for site in sites:
        res = compute_site_year(db, org_id=org_id, site_id=site.id, year=year, region=region)
        total_grid += res.total_grid_kwh
        total_solar += res.total_solar_kwh

    ef = _get_approved_ef(db, region, year)
    ef_val = float(ef.factor_t_per_kwh) if ef else 0.0

    gross = total_grid * ef_val
    avoided = total_solar * ef_val
    net = gross - avoided
    denom = total_grid + total_solar
    renewable_pct = (total_solar / denom * 100.0) if denom > 0 else 0.0

    return ESGAnnualResult(
        year=year,
        total_grid_kwh=float(total_grid),
        total_solar_kwh=float(total_solar),
        gross_scope2_tco2e=round(gross, 4),
        avoided_emissions_tco2e=round(avoided, 4),
        net_scope2_tco2e=round(net, 4),
        renewable_percentage=round(renewable_pct, 2),
        energy_intensity=None,  # org-level needs aggregated production units if you want it
        methodology="GHG Protocol Scope 2 (location-based)",
        emission_factor_t_per_kwh=ef_val,
        emission_factor_version=int(ef.version) if ef else None,
        emission_factor_source=ef.source if ef else None,
    )

def compute_yoy_delta(db: Session, *, org_id: int, site_id: int, year: int, region: str = "default") -> Dict[str, float]:
    cur = compute_site_year(db, org_id=org_id, site_id=site_id, year=year, region=region)
    prev = compute_site_year(db, org_id=org_id, site_id=site_id, year=year-1, region=region)
    return {
        "current_net_scope2_tco2e": cur.net_scope2_tco2e,
        "previous_net_scope2_tco2e": prev.net_scope2_tco2e,
        "delta_net_scope2_tco2e": round(cur.net_scope2_tco2e - prev.net_scope2_tco2e, 4),
    }
