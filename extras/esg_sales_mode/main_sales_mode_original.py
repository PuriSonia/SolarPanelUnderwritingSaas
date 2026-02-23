from fastapi import FastAPI, Header, HTTPException
from services.ml_service import MLScoringService
from services.finance_engine import FinancialEngine
from services.risk_translation import translate_integrity_to_financial_risk

# ============================
# CONFIGURATION
# ============================

API_KEY = "CHANGE_ME_DEMO_KEY"

app = FastAPI(title="Carbon-Integrated ESG Risk SaaS (Demo Ready)")

ml_service = MLScoringService(
    "models_storage/xgb_model.json",
    "models_storage/xgb_cross_registry_quality_model_metadata.json"
)

finance_engine = FinancialEngine()

# ============================
# AUTH HELPER
# ============================

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# ============================
# MAIN ENDPOINT
# ============================

@app.post("/analyze_project")
def analyze_project(project: dict, x_api_key: str = Header(None)):

    verify_api_key(x_api_key)

    ml_result = ml_service.score_project(project["ml_features"])

    risk_params = translate_integrity_to_financial_risk(
        ml_result["ci_class"],
        ml_result["probabilities"]
    )

    base_result = finance_engine.base_case(
        **project["financial_inputs"]
    )

    risk_result = finance_engine.risk_adjusted_case(
        **project["financial_inputs"],
        issuance_probability=ml_result["issuance_probability"],
        delay_years=risk_params["delay_years"],
        risk_premium_bps=risk_params["risk_premium_bps"]
    )

    return {
        "integrity": ml_result,
        "base_case": base_result,
        "risk_adjusted": risk_result
    }


from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="static", html=True), name="static")
