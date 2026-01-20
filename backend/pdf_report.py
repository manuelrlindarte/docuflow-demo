# backend/pdf_report.py

from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import textwrap
from datetime import datetime


def generate_pdf_report(
    document_name: str,
    summary: Dict[str, Any],
    results: List[Dict[str, Any]],
    file_hash: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> bytes:
    """
    Genera un PDF sencillo con:
      - Encabezado DocuFlow
      - Metadatos (fecha, hash)
      - Resumen de cumplimiento
      - Detalle por regla (id, nombre, severidad, estado, 1er snippet de evidencia)

    La firma está alineada con la llamada en backend/app.py:
      generate_pdf_report(
          document_name=filename,
          summary=summary,
          results=results,
          file_hash=file_hash,
          generated_at=generated_at,
      )
    """

    # Si no viene fecha, usamos ahora en UTC
    if generated_at is None:
        generated_at = datetime.utcnow().isoformat() + "Z"

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    # -------------------------------------------------
    # Encabezado
    # -------------------------------------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "DocuFlow – Reporte de Validación")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Documento: {document_name}")
    y -= 12
    c.drawString(50, y, f"Generado: {generated_at}")
    y -= 12

    if file_hash:
        c.drawString(50, y, f"Hash SHA-256: {file_hash}")
        y -= 18
    else:
        y -= 10

    # -------------------------------------------------
    # Resumen de cumplimiento
    # -------------------------------------------------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resumen de cumplimiento")
    y -= 16

    c.setFont("Helvetica", 10)
    compliance = summary.get("compliance_percentage", 0.0)
    passed = summary.get("rules_passed", 0)
    total = summary.get("total_rules", 0)
    critical_failed = summary.get("critical_failed", 0)

    c.drawString(50, y, f"Cumplimiento general: {compliance:.1f}%")
    y -= 12
    c.drawString(50, y, f"Reglas OK: {passed}/{total}")
    y -= 12
    c.drawString(50, y, f"Reglas críticas fallidas: {critical_failed}")
    y -= 20

    # -------------------------------------------------
    # Detalle por regla
    # -------------------------------------------------
    for rule in results:
        if y < 100:
            c.showPage()
            y = height - 50

        rule_id = rule.get("id", "")
        name = rule.get("name", "")
        severity = rule.get("severity", "")
        status = rule.get("status", "")
        description = rule.get("description", "")

        c.setFont("Helvetica-Bold", 11)
        c.drawString(
            50,
            y,
            f"{rule_id} - {name} [{severity}] -> {status}",
        )
        y -= 14

        c.setFont("Helvetica", 9)
        # Descripción de la regla
        for line in textwrap.wrap(description, 110):
            if y < 80:
                c.showPage()
                y = height - 50
            c.drawString(60, y, line)
            y -= 11

        # Primer snippet de evidencia si existe
        evidence_list = rule.get("evidence") or []
        if evidence_list:
            snippet = evidence_list[0]
            if isinstance(snippet, dict):
                snippet_text = snippet.get("text", "")
            else:
                snippet_text = str(snippet)

            if snippet_text:
                y -= 6
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(60, y, "Ejemplo de evidencia:")
                y -= 11
                c.setFont("Helvetica", 8)
                for line in textwrap.wrap(snippet_text, 100):
                    if y < 80:
                        c.showPage()
                        y = height - 50
                    c.drawString(70, y, line)
                    y -= 10

        y -= 12

    # Pie y cierre
    if y < 80:
        c.showPage()
        y = height - 50

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
        50,
        40,
        "Este reporte es generado automáticamente como apoyo al proceso de compliance. "
        "La decisión final sobre cumplimiento debe ser tomada por el Oficial de Cumplimiento.",
    )

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes