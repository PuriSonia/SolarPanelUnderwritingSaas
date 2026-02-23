from app.routers import underwriting
from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, ml, sites, solar, tariffs, uploads, financial, esg, analytics, portfolio, emission_factors, audit_logs, reports, stripe_billing, esg_reports, production, forecast_unified

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar Performance + ESG SaaS", version="0.1.0")

app.include_router(auth.router)
app.include_router(sites.router)
app.include_router(solar.router)
app.include_router(tariffs.router)
app.include_router(uploads.router)
app.include_router(financial.router)
app.include_router(forecast_unified.router)
app.include_router(esg.router)
app.include_router(analytics.router)
app.include_router(portfolio.router)

app.include_router(esg_reports.router)
app.include_router(production.router)

app.include_router(emission_factors.router)
app.include_router(audit_logs.router)
app.include_router(reports.router)
app.include_router(stripe_billing.router)
app.include_router(underwriting.router)
app.include_router(ml.router)

@app.get("/health")
def health():
    return {"ok": True}
