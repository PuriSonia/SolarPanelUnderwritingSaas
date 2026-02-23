from fastapi import APIRouter

router = APIRouter(prefix="/forecast", tags=["Forecast"])

@router.get("/demo")
def demo_forecast():
    return {
        "projection": [
            {"year": 1, "generation_kwh": 1000000, "tariff_rate": 8.5, "revenue": 8500000},
            {"year": 2, "generation_kwh": 995000, "tariff_rate": 8.925, "revenue": 8880375}
        ],
        "npv": 28000000,
        "irr": 0.187
    }
