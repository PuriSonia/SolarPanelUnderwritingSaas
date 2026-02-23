from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base

class UnderwritingSnapshot(Base):
    """Stores underwriting-time projections and deterministic risk outputs.
    ML later uses projected vs actual deltas as labels/features.
    """
    __tablename__ = "underwriting_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)

    model_version = Column(String, nullable=False, default="deterministic_v2.0")
    date_underwritten = Column(DateTime, default=datetime.utcnow, index=True)

    projected_annual_kwh = Column(Float, nullable=True)
    projected_revenue = Column(Float, nullable=True)
    projected_opex = Column(Float, nullable=True)
    projected_dscr = Column(Float, nullable=True)
    projected_degradation_rate = Column(Float, nullable=True)

    risk_score = Column(Float, nullable=True)
    risk_grade = Column(String, nullable=True)
    approval_status = Column(String, nullable=True)

    loan_amount = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)

    request_payload = Column(JSON, nullable=True)   # optional raw input
    results_payload = Column(JSON, nullable=True)   # optional computed outputs

    site = relationship("Site")
    user = relationship("User")
    organization = relationship("Organization")


class AssetPerformance(Base):
    """Time-series performance at the site level (monthly recommended)."""
    __tablename__ = "asset_performance"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)

    timestamp = Column(DateTime, index=True, nullable=False)

    actual_kwh = Column(Float, nullable=True)
    actual_revenue = Column(Float, nullable=True)
    actual_opex = Column(Float, nullable=True)
    downtime_hours = Column(Float, nullable=True)

    weather_irradiance = Column(Float, nullable=True)
    grid_price = Column(Float, nullable=True)

    site = relationship("Site")
    organization = relationship("Organization")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)

    event_type = Column(String, nullable=False)  # default, covenant_breach, underperformance, etc.
    event_date = Column(DateTime, default=datetime.utcnow, index=True)

    severity_score = Column(Float, nullable=True)
    recovery_amount = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

    site = relationship("Site")
    organization = relationship("Organization")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)

    date = Column(DateTime, default=datetime.utcnow, index=True)
    maintenance_type = Column(String, nullable=False)
    cost = Column(Float, nullable=True)
    downtime_hours = Column(Float, nullable=True)
    component_replaced = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    site = relationship("Site")
    organization = relationship("Organization")


class RiskModelRegistry(Base):
    __tablename__ = "risk_models"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=True)

    model_name = Column(String, nullable=False, default="site_risk")
    version = Column(String, nullable=False, default="deterministic_v2.0")
    model_type = Column(String, nullable=False, default="deterministic")  # deterministic, hybrid, ml
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_json = Column(JSON, nullable=True)

    organization = relationship("Organization")


class MLPrediction(Base):
    """Stores on-demand ML signals (anomaly / underperformance) for auditability."""
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)

    prediction_type = Column(String, nullable=False)  # anomaly, underperformance
    model_version = Column(String, nullable=False, default="hybrid_scaffold_v1.0")
    score = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    site = relationship("Site")
    user = relationship("User")
    organization = relationship("Organization")
