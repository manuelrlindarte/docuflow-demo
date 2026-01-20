# backend/app.py

from datetime import datetime
import base64

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .rules_engine import evaluate_document
from .rules import get_golden_rule_set
from .pdf_report import generate_pdf_report


app = FastAPI(
    title="DocuFlow Demo 0.2",
    version="0.2.0",
    description="Motor de validación documental con Golden Rule Set 1.0",
)

# -------------------------------------------------------------------
# CORS (para que Streamlit pueda hablar sin problema)
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # en producción se restringe
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# ENDPOINTS BÁSICOS
# -------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "DocuFlow backend 0.2 operativo"}


@app.get("/rules")
def list_rules(document_type: str = "sarlaft"):
    """
    Devuelve el Golden Rule Set 1.0 (en esta demo) para inspección.
    Útil para debugging y para mostrar en demos qué se está evaluando.
    """
    rules = get_golden_rule_set(document_type)
    return {
        "document_type": document_type,
        "total_rules": len(rules),
        "rules": [r.__dict__ for r in rules],
    }


# -------------------------------------------------------------------
# ENDPOINT PRINCIPAL: /validate
# -------------------------------------------------------------------

@app.post("/validate")
async def validate_document(
    file: UploadFile = File(...),
    document_type: str = Form("sarlaft"),
):
    """
    Endpoint que usa el motor de reglas para evaluar el documento cargado.

    Devuelve:
    - summary: métricas de cumplimiento
    - results: detalle por regla (PASS/PARTIAL/FAIL + confidence + evidencia)
    - evidence: JSON estructurado listo para auditoría / Sandbox
    - pdf_base64: reporte PDF embebido en base64
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No se recibió archivo.")

        file_bytes = await file.read()
        filename = file.filename or "documento_sin_nombre"

        # Evalúa el documento con el motor 0.2
        summary, results, evidence_json, file_hash = evaluate_document(
            file_bytes=file_bytes,
            filename=filename,
            document_type=document_type,
        )

        generated_at = evidence_json.get(
            "generated_at",
            datetime.utcnow().isoformat() + "Z",
        )

        # Generar reporte PDF audit-ready
        pdf_bytes = generate_pdf_report(
            document_name=filename,
            summary=summary,
            results=results,
            file_hash=file_hash,
            generated_at=generated_at,
        )
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # Respuesta completa para el frontend
        return {
            "document_name": filename,
            "generated_at": generated_at,
            "file_hash_sha256": file_hash,
            "summary": summary,
            "results": results,
            "evidence": evidence_json,
            "pdf_base64": pdf_b64,
        }

    except HTTPException:
        # Re-lanzar HTTPExceptions tal cual
        raise

    except Exception as e:
        # Cualquier otro error se devuelve como 500
        raise HTTPException(status_code=500, detail=str(e))