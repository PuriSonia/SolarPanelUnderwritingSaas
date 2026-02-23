from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

# ML-ready data engine tables
from . import ml_data_engine  # noqa: F401

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    billing_status = Column(String, default="inactive")  # inactive, trialing, active, past_due, canceled

    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="admin")  # admin, manager, viewer

    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    organization = relationship("Organization", back_populates="users")

    created_at = Column(DateTime, default=datetime.utcnow)


class UnderwritingRun(Base):
    __tablename__ = "underwriting_runs"

    id = Column(Integer, primary_key=True, index=True)

    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # Optional label for UI (e.g. project name)
    name = Column(String, nullable=True)

    # Store original request and computed results for auditability
    request_payload = Column(JSON, nullable=False)
    results_payload = Column(JSON, nullable=False)

    # Track model/schema version used for the run
    model_version = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    organization = relationship("Organization")
    user = relationship("User")

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    organization = relationship("Organization", back_populates="sites")

    solar_systems = relationship("SolarSystem", back_populates="site", cascade="all, delete-orphan")
    tariffs = relationship("Tariff", back_populates="site", cascade="all, delete-orphan")
    grid = relationship("GridConsumption", back_populates="site", cascade="all, delete-orphan")

class SolarSystem(Base):
    __tablename__ = "solar_systems"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    capacity_kw = Column(Float, nullable=False)
    commissioning_date = Column(Date, nullable=True)

    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)
    site = relationship("Site", back_populates="solar_systems")

    generation = relationship("GenerationData", back_populates="solar_system", cascade="all, delete-orphan")

class Tariff(Base):
    __tablename__ = "tariffs"
    __table_args__ = (UniqueConstraint("site_id", name="uq_tariff_site"),)

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)
    tariff_type = Column(String, default="flat")
    rate_per_kwh = Column(Float, nullable=False, default=0.0)
    demand_charge = Column(Float, nullable=True)

    site = relationship("Site", back_populates="tariffs")

class GenerationData(Base):
    __tablename__ = "generation_data"
    __table_args__ = (UniqueConstraint("solar_system_id", "month", name="uq_gen_system_month"),)

    id = Column(Integer, primary_key=True)
    solar_system_id = Column(Integer, ForeignKey("solar_systems.id"), index=True, nullable=False)
    month = Column(String, nullable=False)  # YYYY-MM
    generation_kwh = Column(Float, nullable=False, default=0.0)

    solar_system = relationship("SolarSystem", back_populates="generation")

class GridConsumption(Base):
    __tablename__ = "grid_consumption"
    __table_args__ = (UniqueConstraint("site_id", "month", name="uq_grid_site_month"),)

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)
    month = Column(String, nullable=False)
    grid_kwh = Column(Float, nullable=False, default=0.0)

    site = relationship("Site", back_populates="grid")

class EmissionFactor(Base):
    __tablename__ = "emission_factors"
    __table_args__ = (UniqueConstraint("region", "version", name="uq_ef_region_version"),)

    id = Column(Integer, primary_key=True)
    region = Column(String, index=True, nullable=False)
    factor_t_per_kwh = Column(Float, nullable=False)  # tCO2e/kWh
    source = Column(String, nullable=True)
    version = Column(Integer, nullable=False, default=1)

    status = Column(String, default="draft")  # draft, approved, retired
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class ProductionData(Base):
    __tablename__ = "production_data"
    __table_args__ = (UniqueConstraint("site_id", "year", name="uq_prod_site_year"),)

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, nullable=False)
    year = Column(Integer, nullable=False)
    production_units = Column(Float, nullable=False, default=0.0)

    site = relationship("Site")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String, nullable=False)
    entity = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="audit_logs")
