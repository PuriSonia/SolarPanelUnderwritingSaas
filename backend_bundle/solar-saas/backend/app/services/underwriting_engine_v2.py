def calculate_risk(projected_dscr, projected_degradation_rate, projected_revenue):
    score = 0
    if projected_dscr < 1.2:
        score += 0.4
    elif projected_dscr < 1.4:
        score += 0.2
    if projected_degradation_rate > 0.01:
        score += 0.2
    if projected_revenue < 0:
        score += 0.3
    return round(score, 2)

MODEL_VERSION = "deterministic_v2.0"
