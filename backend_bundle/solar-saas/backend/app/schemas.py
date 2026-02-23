from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SiteCreate(BaseModel):
    name: str
    location: Optional[str] = None

class SolarSystemCreate(BaseModel):
    site_id: int
    name: str
    capacity_kw: float

class TariffUpsert(BaseModel):
    site_id: int
    rate_per_kwh: float
    tariff_type: str = "flat"
    demand_charge: Optional[float] = None

class EmissionFactorCreate(BaseModel):
    region: str
    factor_t_per_kwh: float
    source: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None

class EmissionFactorApprove(BaseModel):
    id: int


# ---------------------------
# Underwriting (ESG + IRR) schemas
# ---------------------------
from typing import Optional, Any, Dict

class UnderwritingAnalyzeRequest(BaseModel):
    name: Optional[str] = None
    ml_features: Dict[str, Any]
    financial_inputs: Dict[str, Any]

class UnderwritingRunOut(BaseModel):
    id: int
    org_id: int
    user_id: int
    name: Optional[str] = None
    model_version: Optional[str] = None
    request_payload: Dict[str, Any]
    results_payload: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
