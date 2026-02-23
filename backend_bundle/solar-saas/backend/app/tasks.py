import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from .celery_app import celery_app
from .database import SessionLocal
from .models import Site, SolarSystem, GenerationData, GridConsumption, Tariff, EmissionFactor
from .reporting import generate_investor_pdf

def _db() -> Session:
    return SessionLocal()

@celery_app.task(name="tasks.generate_site_report")
def generate_site_report(org_id: int, site_id: int, year: str, region: str = "default"):
    db = _db()
    try:
        site = db.query(Site).filter(Site.id == site_id, Site.org_id == org_id).first()
        if not site:
            return {"ok": False, "error": "site not found"}

        systems = db.query(SolarSystem).filter(SolarSystem.site_id == site_id).all()
        tariff = db.query(Tariff).filter(Tariff.site_id == site_id).first()
        rate = tariff.rate_per_kwh if tariff else 0.0

        ef = (
            db.query(EmissionFactor)
            .filter(EmissionFactor.region == region, EmissionFactor.status == "approved")
            .order_by(EmissionFactor.version.desc())
            .first()
        )
        ef_val = ef.factor_t_per_kwh if ef else 0.0

        months = [f"{year}-{m:02d}" for m in range(1, 13)]
        gen_by_month = {m: 0.0 for m in months}
        grid_by_month = {m: 0.0 for m in months}

        for system in systems:
            rows = db.query(GenerationData.month, GenerationData.generation_kwh).filter(
                GenerationData.solar_system_id == system.id,
                GenerationData.month.in_(months),
            ).all()
            for month, kwh in rows:
                gen_by_month[month] += float(kwh or 0)

        rows = db.query(GridConsumption.month, GridConsumption.grid_kwh).filter(
            GridConsumption.site_id == site_id,
            GridConsumption.month.in_(months),
        ).all()
        for month, kwh in rows:
            grid_by_month[month] += float(kwh or 0)

        total_gen = sum(gen_by_month.values())
        total_grid = sum(grid_by_month.values())
        savings = total_gen * rate

        gross_scope2_t = total_grid * ef_val
        avoided_t = total_gen * ef_val
        net_scope2_t = gross_scope2_t - avoided_t

        storage_dir = os.getenv("STORAGE_DIR", "./storage")
        out_path = os.path.join(storage_dir, "reports", f"site_{site_id}_{year}.pdf")

        sections = [
            {"heading": "Overview", "lines": [
                f"Site: {site.name}",
                f"Location: {site.location or '-'}",
                f"Year: {year}",
            ]},
            {"heading": "Energy Performance", "lines": [
                f"Total solar generation: {total_gen:,.0f} kWh",
                f"Total grid consumption: {total_grid:,.0f} kWh",
            ]},
            {"heading": "Financial Impact (Estimated)", "lines": [
                f"Tariff rate: {rate:.4f} per kWh",
                f"Estimated savings: {savings:,.2f}",
            ]},
            {"heading": "GHG Impact (Scope 2, location-based)", "lines": [
                f"Emission factor (tCO2/kWh): {ef_val:.6f} (region={region}, version={ef.version if ef else 'n/a'})",
                f"Gross Scope 2: {gross_scope2_t:,.2f} tCO2e",
                f"Avoided by solar: {avoided_t:,.2f} tCO2e",
                f"Net Scope 2: {net_scope2_t:,.2f} tCO2e",
            ]},
        ]

        generate_investor_pdf(out_path, "Solar Performance & ESG Summary", sections)
        return {"ok": True, "path": out_path}
    finally:
        db.close()
