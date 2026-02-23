from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Site, User
from app.ml_data_engine import MLPrediction
from app.services.ml_scoring import HybridMLScoringService

router = APIRouter(prefix="/ml", tags=["ml"])

def _ensure_site_access(db: Session, user: User, site_id: int) -> Site:
    site = db.query(Site).filter(Site.id == site_id, Site.org_id == user.org_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.get("/sites/{site_id}/anomaly")
def anomaly(site_id: int, persist: bool = True, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_site_access(db, user, site_id)
    svc = HybridMLScoringService(db, user.org_id)
    res = svc.anomaly(site_id)
    payload = {"type": "anomaly", "model_version": svc.MODEL_VERSION, "score": res.anomaly_score, "reasons": res.reasons, "peers": res.peers}
    if persist:
        row = MLPrediction(org_id=user.org_id, user_id=user.id, site_id=site_id, prediction_type="anomaly", model_version=svc.MODEL_VERSION, score=res.anomaly_score, details=payload)
        db.add(row); db.commit()
    return payload

@router.get("/sites/{site_id}/underperformance")
def underperformance(site_id: int, persist: bool = True, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_site_access(db, user, site_id)
    svc = HybridMLScoringService(db, user.org_id)
    res = svc.underperformance(site_id)
    payload = {"type": "underperformance", "model_version": svc.MODEL_VERSION, "probability": res.probability, "ratio_actual_to_projected": res.ratio_actual_to_projected, "reasons": res.reasons}
    if persist:
        row = MLPrediction(org_id=user.org_id, user_id=user.id, site_id=site_id, prediction_type="underperformance", model_version=svc.MODEL_VERSION, score=res.probability, details=payload)
        db.add(row); db.commit()
    return payload

@router.get("/sites/{site_id}/predictions")
def list_predictions(site_id: int, limit: int = 25, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_site_access(db, user, site_id)
    rows = (db.query(MLPrediction)
            .filter(MLPrediction.org_id == user.org_id, MLPrediction.site_id == site_id)
            .order_by(MLPrediction.created_at.desc())
            .limit(limit)
            .all())
    return [
        {
            "id": r.id,
            "prediction_type": r.prediction_type,
            "model_version": r.model_version,
            "score": r.score,
            "created_at": r.created_at,
            "details": r.details,
        } for r in rows
    ]
