# Solar Performance + ESG SaaS (Starter)

Multi-tenant FastAPI + Postgres starter that includes:
- Financial savings engine
- Scope 2 emissions module
- Full registration/login (JWT)
- Emission factor versioning + approvals
- Role-based access control
- Audit logging
- Background processing (Celery + Redis)
- Investor-grade PDF reporting
- Stripe billing scaffolding

## Run with Docker
```bash
docker-compose up --build
```

API docs:
- http://localhost:8000/docs

## Try it quickly
1) `POST /register`
2) Use returned `access_token` in Swagger "Authorize" (Bearer token)
3) Create a site, solar system, tariff
4) Upload CSVs:
   - `/upload/generation/{solar_system_id}` columns: month,generation_kwh
   - `/upload/grid/{site_id}` columns: month,grid_kwh
5) Create and approve an emission factor (region=default)
6) Generate a report:
   - `POST /reports/site/{site_id}/year/2026`
   - `GET /reports/task/{task_id}` to see the PDF path

## Notes
- PDFs are stored in STORAGE_DIR/reports (mounted as docker volume `storage`).
- Stripe endpoints need STRIPE env vars configured.
