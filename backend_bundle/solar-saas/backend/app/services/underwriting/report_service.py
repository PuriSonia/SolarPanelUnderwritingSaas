from __future__ import annotations

from io import BytesIO
from typing import Dict, Any
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors


def build_underwriting_report(payload: Dict[str, Any], results: Dict[str, Any]) -> bytes:
    """
    Create a client-ready underwriting PDF report.

    payload: original request (ml_features + financial_inputs)
    results: response from /api/analyze_project (integrity + base_case + risk_adjusted)
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, title="Carbon-Integrated ESG Underwriting Summary")
    styles = getSampleStyleSheet()
    title = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    elements = []
    elements.append(Paragraph("Carbon-Integrated ESG Underwriting Summary", title))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body))
    elements.append(Spacer(1, 0.2 * inch))

    integrity = results.get("integrity", {})
    base_case = results.get("base_case", {})
    risk_adj = results.get("risk_adjusted", {})

    # Executive summary
    ci = integrity.get("ci_class", "—")
    issuance = integrity.get("issuance_probability", None)
    base_irr = base_case.get("irr", None)
    risk_irr = risk_adj.get("irr", None)

    def fmt_pct(x):
        try:
            return f"{float(x)*100:.2f}%"
        except Exception:
            return "—"

    def fmt_num(x):
        try:
            return f"{float(x):,.2f}"
        except Exception:
            return "—"

    bps_delta = "—"
    try:
        bps_delta = f"{(float(risk_irr)-float(base_irr))*10000:.0f} bps"
    except Exception:
        pass

    elements.append(Paragraph("Executive Summary", h2))
    if isinstance(issuance, (int, float)):
        summary_txt = (
            f"This analysis integrates carbon integrity risk into project financial returns. "
            f"Integrity Class: <b>{ci}</b>. "
            f"Issuance Probability: <b>{issuance:.2f}</b>."
        )
    else:
        summary_txt = (
            f"This analysis integrates carbon integrity risk into project financial returns. "
            f"Integrity Class: <b>{ci}</b>."
        )
    elements.append(Paragraph(summary_txt, body))
    elements.append(Spacer(1, 0.15 * inch))

    # Key metrics table
    elements.append(Paragraph("Key Return Metrics", h2))
    data = [
        ["Metric", "Base Case", "Risk-Adjusted"],
        ["IRR", fmt_pct(base_irr), fmt_pct(risk_irr)],
        ["NPV", fmt_num(base_case.get("npv")), fmt_num(risk_adj.get("npv"))],
        ["IRR Impact", "", bps_delta],
        ["Adjusted Discount Rate", "", fmt_pct(risk_adj.get("adjusted_discount_rate"))],
    ]

    tbl = Table(data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.2 * inch))

    # Inputs snapshot
    elements.append(Paragraph("Inputs Snapshot", h2))
    fin = payload.get("financial_inputs", {})
    ml = payload.get("ml_features", {})

    inputs_data = [
        ["Section", "Field", "Value"],
        ["Financial", "Capex", fmt_num(fin.get("capex"))],
        ["Financial", "Energy Revenue (annual)", fmt_num(fin.get("energy_revenue"))],
        ["Financial", "Carbon Revenue (annual)", fmt_num(fin.get("carbon_revenue"))],
        ["Financial", "Opex (annual)", fmt_num(fin.get("opex"))],
        ["Financial", "Years", str(fin.get("years", "—"))],
        ["Financial", "Discount Rate", fmt_pct(fin.get("discount_rate"))],
        ["Integrity ML", "registry", str(ml.get("registry", "—"))],
        ["Integrity ML", "project_type", str(ml.get("project_type", "—"))],
        ["Integrity ML", "methodology", str(ml.get("methodology", "—"))],
        ["Integrity ML", "country", str(ml.get("country", "—"))],
        ["Integrity ML", "est_annual_er", fmt_num(ml.get("est_annual_er"))],
        ["Integrity ML", "Crediting_Years", str(ml.get("Crediting_Years", "—"))],
        ["Integrity ML", "ProjReg_Year", str(ml.get("ProjReg_Year", "—"))],
    ]
    inputs_tbl = Table(inputs_data, colWidths=[1.2*inch, 2.4*inch, 2.4*inch])
    inputs_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    elements.append(inputs_tbl)

    doc.build(elements)
    return buf.getvalue()
