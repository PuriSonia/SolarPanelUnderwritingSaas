# Solar SaaS Runbook (Developer)

Last updated: 2026-02-14

This runbook covers the **production-demo stack**:
- **Backend:** FastAPI + Postgres (`solar-saas-unified-backend-patched`)
- **Frontend:** Next.js dashboard (`solar-saas-dashboard-pro-enterprise`)

The goal is to get a **client-demo-ready** system running locally (and easily deployable later).

---

## 1) Repo Layout

### Backend (FastAPI)
Typical paths (may vary slightly by zip):
- `solar-saas/backend/` – backend root
- `solar-saas/backend/app/main.py` – app entrypoint, router registration
- `solar-saas/backend/app/models.py` – DB tables
- `solar-saas/backend/app/routers/` – API endpoints
- `solar-saas/backend/app/services/` – business logic engines (ESG, forecasting)
- `solar-saas/docker-compose.yml` – Postgres + backend (if present)

### Frontend (Next.js)
- `solar-saas-frontend/` – frontend root
- `app/` – routes (dashboard, sites, uploads)
- `lib/` – API clients (`api.ts`, `upload.ts`, `enterprise.ts`)
- `.env.local` – points to backend URL

---

## 2) Environment Variables

### Backend (.env)
Create `solar-saas/backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/solar_saas

# Auth / JWT (use strong values in real production)
JWT_SECRET=change_me_to_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=120

# CORS (frontend URL)
CORS_ORIGINS=http://localhost:3000
```

> If your backend currently reads a different env var name for the secret (e.g. `SECRET_KEY`), align it in `app/security.py` or `app/auth.py`.

### Frontend (.env.local)
Create `solar-saas-frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 3) Local Setup (Fastest Path)

### 3.1 Start Postgres
Option A — Docker (recommended):
```bash
docker compose up -d db
```

Option B — Local Postgres:
- Create DB `solar_saas`
- Ensure `postgres:postgres` (or update `DATABASE_URL`)

### 3.2 Run Backend
From backend folder (where `requirements.txt` exists):
```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open:
- Swagger: `http://localhost:8000/docs`
- Health (if present): `http://localhost:8000/health`

### 3.3 Run Frontend
From frontend folder:
```bash
npm install
npm run dev
```

Open:
- `http://localhost:3000`

---

## 4) DB Migrations Plan (Recommended)

Right now the demo stack often uses `Base.metadata.create_all(...)` for convenience.
For a real production path:

1) Add Alembic:
```bash
pip install alembic
alembic init alembic
```

2) Configure `alembic.ini` with `DATABASE_URL`

3) Point Alembic to your SQLAlchemy `Base` in `alembic/env.py`

4) Generate migrations:
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

5) Thereafter, whenever models change:
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

**Rule:** once you have client data, do NOT rely on `create_all()` for schema changes.

---

## 5) Seed Data (Demo Mode)

### 5.1 Create a demo org + user
Use the API:
- `POST /register`
- `POST /login`

Then use the token for subsequent calls.

### 5.2 Create a site
- `POST /sites` (name, location)

### 5.3 Create a solar system
- `POST /solar` (site_id, name, capacity_kw)

### 5.4 Set tariff
- `POST /tariffs/upsert` (site_id, rate_per_kwh)

### 5.5 Add emission factor
- `POST /emission-factors` or `/emission-factors/upsert` (depending on router)
  - region: `default`
  - factor in **tCO2e per kWh**
  - source: e.g. "CEA India (year)"

Approve it if your model supports approvals.

### 5.6 Upload data (CSV)
From the UI:
- `/uploads` page

CSV formats:
- Generation: `month,generation_kwh` (month = `YYYY-MM`)
- Grid: `month,grid_kwh`

### 5.7 Validate outputs
- Site analytics charts populate
- ESG scorecard works:
  - `GET /esg-reports/site/{site_id}/scorecard?year=YYYY`
- Forecast works:
  - `GET /forecast/...` endpoint used by UI

---

## 6) First Client Onboarding Checklist (Commercial)

**Goal:** a repeatable 30–60 min onboarding.

1) Create org + admin user  
2) Create site(s)  
3) Create solar system(s) + capacity  
4) Confirm tariff rate (₹/kWh)  
5) Set emission factor (region + source)  
6) Upload last 12 months:
   - grid consumption
   - solar generation (per system)
7) Verify:
   - savings calculation matches expectations
   - renewable % is plausible
   - Scope 2 net emissions make sense
8) Generate:
   - ESG scorecard screenshot/PDF (demo)
   - forecast chart screenshot (demo)

**Deliverable for client:** “Month-1 report” (performance + savings + ESG summary).

---

## 7) Common Failure Fixes

### 7.1 CORS errors
Symptom: frontend shows network errors, backend blocks request.

Fix:
- Set `CORS_ORIGINS=http://localhost:3000`
- Ensure `app/main.py` enables CORS middleware.
- Restart backend.

### 7.2 401 Unauthorized / token issues
- Confirm login returns token.
- Confirm frontend stores token (LocalStorage).
- Ensure backend expects `Authorization: Bearer <token>`.

### 7.3 DB connection errors
- Confirm Postgres running (`docker ps`)
- Confirm DB exists
- Confirm `DATABASE_URL` is correct
- Check firewall/port mapping if using Docker

### 7.4 “No data” in charts
- Upload CSVs for the correct site/system IDs
- Ensure months are `YYYY-MM`
- Ensure values are numeric
- Recheck that the UI is pointing to correct backend base URL

### 7.5 Emissions show 0
- Emission factor missing or not approved (depending on model)
- Region mismatch (`default` vs other)
- Ensure factor units: **tCO2e/kWh** (not kg)

---

## 8) What To Build Next (Bank Credibility Path)

If you are pitching lenders:
- Move forecasting from demo endpoint to real DB inputs:
  - baseline generation = last 12 months
  - CAPEX, OPEX, degradation, inflation, discount rate
- Add scenario toggle (base/conservative/upside)
- Add DSCR + debt schedule
- Add lender-grade backend PDF export
- Add reporting period locking + audit trails

---

## 9) Quick “Is it working?” Smoke Test

1) Backend docs load: `http://localhost:8000/docs`
2) Frontend loads: `http://localhost:3000`
3) Register + login works
4) Create site + solar system
5) Upload CSVs
6) Dashboard shows:
   - savings
   - ESG scorecard
   - forecast chart

If all 6 pass, you have a working demo.

---
