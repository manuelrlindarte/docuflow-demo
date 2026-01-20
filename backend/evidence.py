# backend/evidence.py

from typing import List, Dict, Any
from datetime import datetime
import hashlib


def compute_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula el resumen de cumplimiento a partir de la lista de resultados de reglas.
    """
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "PASS")
    critical_failed = sum(
        1
        for r in results
        if r.get("severity") == "CRITICA" and r.get("status") != "PASS"
    )

    if total > 0:
        compliance = (passed / total) * 100.0
    else:
        compliance = 0.0

    return {
        "total_rules": total,
        "rules_passed": passed,
        "compliance_percentage": compliance,
        "critical_failed": critical_failed,
    }


def build_evidence_json(
    document_name: str,
    file_bytes: bytes,
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Construye el JSON de evidencia que consumirá el frontend.
    NO requiere 'summary' como parámetro: lo calcula internamente.
    """
    # Hash del archivo para trazabilidad
    file_hash = None
    if file_bytes:
        file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Resumen de cumplimiento
    summary = compute_summary(results)

    evidence: Dict[str, Any] = {
        "document_name": document_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "file_hash_sha256": file_hash,
        "summary": summary,
        "results": results,  # lista de reglas con status, evidencia, etc.
        "evidence": {
            "rules": results,
            "hash": file_hash,
        },
    }

    return evidence