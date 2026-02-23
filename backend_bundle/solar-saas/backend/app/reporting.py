import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def generate_investor_pdf(path: str, title: str, sections: List[Dict[str, Any]]):
    ensure_dir(os.path.dirname(path))
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    y = height - 72
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, y, title)
    y -= 22

    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 28

    for sec in sections:
        if y < 120:
            c.showPage()
            y = height - 72

        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, y, sec.get("heading", "Section"))
        y -= 16

        c.setFont("Helvetica", 10)
        for line in sec.get("lines", []):
            if y < 90:
                c.showPage()
                y = height - 72
                c.setFont("Helvetica", 10)
            c.drawString(90, y, str(line))
            y -= 14

        y -= 10

    c.showPage()
    c.save()
