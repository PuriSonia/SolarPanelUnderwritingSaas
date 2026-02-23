from __future__ import annotations

from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import UnderwritingRun, User
from app.schemas import UnderwritingAnalyzeRequest, UnderwritingRunOut

from app.services.underwriting.ml_service_upgraded import MLScoringService
from app.services.underwriting.finance_engine import FinancialEngine
from app.services.underwriting.risk_translation import translate_integrity_to_financial_risk
from app.services.underwriting.report_service import build_underwriting_report

router = APIRouter(prefix="/underwriting", tags=["underwriting"])

_ml_service: Optional[MLScoringService] = None
_fin_engine = FinancialEngine()


def _get_ml_service() -> MLScoringService:
    global _ml_service
    if _ml_service is None:
        _ml_service = MLScoringService(
            "app/services/underwriting/xgb_model.json",
            "app/services/underwriting/xgb_cross_registry_quality_model_metadata.json",
        )
    return _ml_service


def _ensure_org_access(user: User, run: UnderwritingRun) -> None:
    if run.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Run not found")


@router.post("/analyze", response_model=UnderwritingRunOut)
def analyze_and_store(
    payload: UnderwritingAnalyzeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "manager")),
):
    """
    Analyze a project and persist an underwriting run (per org/user).

    Input:
      { name?, ml_features: {...}, financial_inputs: {...} }

    Output:
      UnderwritingRunOut (includes stored request + results)
    """
    ml_service = _get_ml_service()

    ml_result = ml_service.score_project(payload.ml_features)

    risk_params = translate_integrity_to_financial_risk(
        ml_result["ci_class"],
        ml_result.get("probabilities", {}),
    )

    base_result = _fin_engine.base_case(**payload.financial_inputs)

    risk_result = _fin_engine.risk_adjusted_case(
        **payload.financial_inputs,
        issuance_probability=ml_result["issuance_probability"],
        delay_years=risk_params["delay_years"],
        risk_premium_bps=risk_params["risk_premium_bps"],
    )

    results = {"integrity": ml_result, "base_case": base_result, "risk_adjusted": risk_result}

    run = UnderwritingRun(
        org_id=user.org_id,
        user_id=user.id,
        name=payload.name,
        request_payload={"name": payload.name, "ml_features": payload.ml_features, "financial_inputs": payload.financial_inputs},
        results_payload=results,
        model_version=getattr(getattr(ml_service, "schema", None), "version", None),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=List[UnderwritingRunOut])
def list_runs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 50,
):
    q = (
        db.query(UnderwritingRun)
        .filter(UnderwritingRun.org_id == user.org_id)
        .order_by(UnderwritingRun.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    return q.all()


@router.get("/runs/{run_id}", response_model=UnderwritingRunOut)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = db.query(UnderwritingRun).filter(UnderwritingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    _ensure_org_access(user, run)
    return run


@router.get("/runs/{run_id}/report")
def get_run_report(
    run_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = db.query(UnderwritingRun).filter(UnderwritingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    _ensure_org_access(user, run)

    pdf_bytes = build_underwriting_report(run.request_payload, run.results_payload)
    filename = f"underwriting_run_{run_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
