import numpy as np

def calculate_forecast(base_generation_kwh, tariff_rate,
                       degradation_rate, tariff_inflation,
                       discount_rate, capex, years=5):

    generation = base_generation_kwh
    rate = tariff_rate
    cash_flows = []
    projection = []

    for year in range(1, years + 1):
        revenue = generation * rate
        cash_flows.append(revenue)

        projection.append({
            "year": year,
            "generation_kwh": round(generation, 2),
            "tariff_rate": round(rate, 4),
            "revenue": round(revenue, 2)
        })

        generation *= (1 - degradation_rate)
        rate *= (1 + tariff_inflation)

    npv = -capex + sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))

    try:
        irr = float(np.irr([-capex] + cash_flows))
    except:
        irr = None

    return {
        "projection": projection,
        "cash_flows": cash_flows,
        "npv": round(npv, 2),
        "irr": round(irr, 4) if irr else None
    }
