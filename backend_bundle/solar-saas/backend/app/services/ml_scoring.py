from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from sqlalchemy.orm import Session

from app.models import Site, SolarSystem, GenerationData
from app.ml_data_engine import UnderwritingSnapshot, AssetPerformance

@dataclass
class AnomalyResult:
    anomaly_score: float  # 0..1
    reasons: List[str]
    peers: Dict[str, float]

@dataclass
class UnderperformanceResult:
    probability: float  # 0..1
    ratio_actual_to_projected: Optional[float]
    reasons: List[str]

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _safe_div(a: float, b: float) -> Optional[float]:
    if b is None or b == 0:
        return None
    return a / b

def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))

class HybridMLScoringService:
    """Lightweight ML scaffold.
    Uses robust statistics over tenant peers and projection-vs-actual deltas.
    No training pipeline yet; designed to be replaced by a trained model later.
    """
    MODEL_VERSION = "hybrid_scaffold_v1.0"

    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id

    def _site_capacity_kw(self, site_id: int) -> float:
        q = self.db.query(SolarSystem).filter(SolarSystem.site_id == site_id).all()
        return float(sum([s.capacity_kw or 0.0 for s in q]))

    def _last_12mo_kwh(self, site_id: int) -> Optional[float]:
        # Prefer new AssetPerformance if present; fall back to GenerationData.
        perf = (
            self.db.query(AssetPerformance)
            .filter(AssetPerformance.org_id == self.org_id, AssetPerformance.site_id == site_id)
            .order_by(AssetPerformance.timestamp.desc())
            .limit(12)
            .all()
        )
        if perf:
            return float(sum([(p.actual_kwh or 0.0) for p in perf]))
        # fallback: generation_data has month column; take latest 12 rows
        gen = (
            self.db.query(GenerationData)
            .join(SolarSystem, GenerationData.solar_system_id == SolarSystem.id)
            .filter(SolarSystem.site_id == site_id)
            .order_by(GenerationData.month.desc())
            .limit(12)
            .all()
        )
        if not gen:
            return None
        return float(sum([(g.kwh or 0.0) for g in gen]))

    def _projected_annual_kwh(self, site_id: int) -> Optional[float]:
        snap = (
            self.db.query(UnderwritingSnapshot)
            .filter(UnderwritingSnapshot.org_id == self.org_id, UnderwritingSnapshot.site_id == site_id)
            .order_by(UnderwritingSnapshot.date_underwritten.desc())
            .first()
        )
        if not snap:
            return None
        return snap.projected_annual_kwh

    def anomaly(self, site_id: int) -> AnomalyResult:
        # Peer distribution based on capacity_kw and realized kwh (12mo)
        peers = (
            self.db.query(Site)
            .filter(Site.org_id == self.org_id)
            .all()
        )
        caps = []
        kwhs = []
        for s in peers:
            caps.append(self._site_capacity_kw(s.id))
            k = self._last_12mo_kwh(s.id)
            kwhs.append(float(k or 0.0))

        target_cap = self._site_capacity_kw(site_id)
        target_kwh = float(self._last_12mo_kwh(site_id) or 0.0)

        def robust_z(value: float, arr: List[float]) -> float:
            arr2 = sorted(arr)
            if not arr2:
                return 0.0
            med = arr2[len(arr2)//2]
            mad = sorted([abs(x - med) for x in arr2])[len(arr2)//2] or 1e-9
            return (value - med) / (1.4826 * mad)

        z_cap = robust_z(target_cap, caps)
        z_kwh = robust_z(target_kwh, kwhs)

        # anomaly score: high if far from peers in either dimension
        raw = max(abs(z_cap), abs(z_kwh))
        anomaly_score = _clamp01(raw / 4.0)  # 4 robust-z ~= very unusual

        reasons = []
        if abs(z_cap) > 2.5:
            reasons.append("Installed capacity is unusual vs other sites in your portfolio.")
        if abs(z_kwh) > 2.5:
            reasons.append("Recent energy output is unusual vs other sites in your portfolio.")
        if not reasons:
            reasons.append("No strong anomalies detected; site looks similar to portfolio peers.")

        peer_stats = {
            "target_capacity_kw": target_cap,
            "target_last12mo_kwh": target_kwh,
        }
        return AnomalyResult(anomaly_score=anomaly_score, reasons=reasons, peers=peer_stats)

    def underperformance(self, site_id: int) -> UnderperformanceResult:
        projected = self._projected_annual_kwh(site_id)
        actual_12 = self._last_12mo_kwh(site_id)
        ratio = None
        reasons = []

        if projected is None or actual_12 is None:
            reasons.append("Not enough data to compare projected vs actual. Add an underwriting snapshot and monthly performance.")
            return UnderperformanceResult(probability=0.5, ratio_actual_to_projected=None, reasons=reasons)

        ratio = _safe_div(actual_12, projected)
        if ratio is None:
            reasons.append("Projected production is missing/zero.")
            return UnderperformanceResult(probability=0.5, ratio_actual_to_projected=None, reasons=reasons)

        # Simple logistic mapping around 1.0 with slope; <0.9 starts to rise quickly
        z = (0.95 - ratio) * 8.0  # ratio=0.95 => z=0, ratio=0.80 => z=1.2
        prob = _clamp01(_sigmoid(z))

        if ratio < 0.9:
            reasons.append("Actual energy output is materially below projection over the last 12 months.")
        elif ratio < 1.0:
            reasons.append("Actual energy output is slightly below projection; monitor performance.")
        else:
            reasons.append("Actual energy output meets or exceeds projection over the last 12 months.")

        return UnderperformanceResult(probability=prob, ratio_actual_to_projected=ratio, reasons=reasons)
