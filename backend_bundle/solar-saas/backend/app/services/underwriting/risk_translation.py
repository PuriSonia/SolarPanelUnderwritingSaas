
def translate_integrity_to_financial_risk(ci_class, probabilities):

    risk_mapping = {
        "A": {"delay": 0, "premium": 50},
        "B": {"delay": 1, "premium": 200},
        "C": {"delay": 2, "premium": 400}
    }

    base = risk_mapping.get(ci_class)

    return {
        "delay_years": base["delay"],
        "risk_premium_bps": base["premium"]
    }
