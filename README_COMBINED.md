# Solar SaaS + ESG Underwriting (Unified, Enterprise Fit #1)

This bundle combines:
1. **Solar SaaS main stack with runbook** (full platform: frontend + backend + infra/runbook)
2. **Unified backend patched** (canonical backend fork swapped into the main stack)
3. **ESG Risk SaaS Sales Mode** integrated as a first-class **Underwriting** module inside the backend.

## What you get

### One product, one login, one database
The platform's existing authentication/multi-tenancy stays in place. The ESG underwriting engine is added as a new router and service module.

### New backend module: Underwriting
- Router: `backend_bundle/solar-saas/backend/app/routers/underwriting.py`
- Services: `backend_bundle/solar-saas/backend/app/services/underwriting/*`

Endpoints (JWT-auth via the platform):
- `POST /underwriting/analyze`
  - body: `{ "ml_features": {...}, "financial_inputs": {...} }`
  - returns: `{ integrity, base_case, risk_adjusted }`
- `POST /underwriting/report`
  - body: `{ "payload": <request>, "results": <analyze response> }`
  - returns: PDF bytes (`application/pdf`)

## Where the original Sales Mode demo assets are kept
For reference/demo reuse:
- `extras/esg_sales_mode/index.html`
- `extras/esg_sales_mode/main_sales_mode_original.py`
- `extras/esg_sales_mode/SALES_DEMO_SCRIPT.txt`

## Model artifacts
The XGBoost model and metadata are copied into:
`backend_bundle/solar-saas/backend/app/services/underwriting/`

If you prefer to store these in S3/registry, update `_get_ml_service()` in the underwriting router.

## How to run
Use the original runbook from the main stack. This combined bundle keeps the same folder layout:
- `backend_bundle/` for backend services
- `frontend_bundle/` for the dashboard UI

If your runbook uses docker-compose at repo root, run it from this combined folder.

## Notes / Next steps
- Persist underwriting runs per org/user (DB table) and expose history in the dashboard.
- Add role-based access controls for underwriting endpoints.
- Move model init to `app.state` on startup for multi-worker deployments.


## Underwriting runs (persistence + dashboard)
- Backend now persists runs in `underwriting_runs` table.
- New endpoints: `GET /underwriting/runs`, `GET /underwriting/runs/{id}`, `GET /underwriting/runs/{id}/report`.
- Frontend page: `/underwriting` provides an institutional-style report view and history.
