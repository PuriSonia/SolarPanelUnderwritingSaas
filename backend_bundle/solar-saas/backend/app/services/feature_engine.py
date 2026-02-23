def compute_basic_features(performance_records):
    if not performance_records:
        return {}
    total_kwh = sum(p.actual_kwh for p in performance_records if p.actual_kwh)
    avg_kwh = total_kwh / len(performance_records)
    return {
        "avg_production": avg_kwh,
        "data_points": len(performance_records)
    }
