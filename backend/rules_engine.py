# backend/rules_engine.py

import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple

from .rules import Rule, get_golden_rule_set
from .text_extractor import extract_text_from_file  # asumiendo que ya lo tienes


def compute_document_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def find_keyword_matches(text: str, rule: Rule) -> List[Dict[str, Any]]:
    """
    Búsqueda simple de keywords. Ya la tenías de alguna forma, aquí la dejamos
    explícita y devolvemos snippets con posición y ratio.
    """
    text_lower = text.lower()
    snippets = []
    for kw in rule.keywords:
        kw_lower = kw.lower()
        start = 0
        while True:
            idx = text_lower.find(kw_lower, start)
            if idx == -1:
                break
            start = idx + len(kw_lower)
            window = 300  # tamaño de snippet
            snippet_start = max(0, idx - window // 2)
            snippet_end = min(len(text), idx + window // 2)
            snippet_text = text[snippet_start:snippet_end]

            snippets.append(
                {
                    "text": snippet_text,
                    "keyword": kw,
                    "position": idx,
                    "position_ratio": round(idx / max(len(text), 1), 3),
                }
            )
    return snippets


def evaluate_rule_with_confidence(text: str, rule: Rule) -> Dict[str, Any]:
    evidences = find_keyword_matches(text, rule)
    matches_found = len(evidences)
    required = max(rule.min_occurrences, 1)

    # Confianza en función de cuántos matches encontramos vs requeridos
    raw_ratio = matches_found / required if required > 0 else 0.0
    confidence = max(0.0, min(100.0, raw_ratio * 100.0))

    if confidence >= 100.0:
        status = "PASS"
    elif confidence >= 50.0:
        status = "PARTIAL"
    else:
        status = "FAIL"

    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "severity": rule.severity,
        "status": status,
        "confidence": round(confidence, 1),
        "matches": matches_found,
        "required_matches": required,
        "evidence": evidences,
        "recommendation": rule.recommendation,
    }


def summarize_results(rule_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_rules = len(rule_results)
    pass_count = sum(1 for r in rule_results if r["status"] == "PASS")
    partial_count = sum(1 for r in rule_results if r["status"] == "PARTIAL")
    fail_count = sum(1 for r in rule_results if r["status"] == "FAIL")

    # Definimos un compliance general ponderando: PASS=1, PARTIAL=0.5, FAIL=0
    score = 0.0
    for r in rule_results:
        if r["status"] == "PASS":
            score += 1.0
        elif r["status"] == "PARTIAL":
            score += 0.5
        else:
            score += 0.0

    compliance_percentage = 0.0
    if total_rules > 0:
        compliance_percentage = (score / total_rules) * 100.0

    critical_failed = sum(
        1
        for r in rule_results
        if r["severity"].upper() == "CRITICA" and r["status"] != "PASS"
    )

    return {
        "total_rules": total_rules,
        "rules_passed": pass_count,
        "rules_partial": partial_count,
        "rules_failed": fail_count,
        "compliance_percentage": round(compliance_percentage, 1),
        "critical_failed": critical_failed,
    }


def build_evidence_json(
    document_name: str,
    file_hash: str,
    summary: Dict[str, Any],
    rule_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Estructura de evidencia pensada para:
    - Oficiales de cumplimiento
    - Auditores
    - Sandbox SFC / Sup. digital
    """
    return {
        "document_name": document_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "file_hash_sha256": file_hash,
        "summary": summary,
        "results": rule_results,
        "evidence": {
            "rules": rule_results,
            "hash": file_hash,
        },
    }


def evaluate_document(
    file_bytes: bytes,
    filename: str,
    document_type: str = "sarlaft",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], str]:
    """
    Función principal que usa el backend.app
    Devuelve:
      - summary
      - results
      - evidence_json
      - file_hash
    """
    text = extract_text_from_file(file_bytes, filename)
    rules = get_golden_rule_set(document_type)

    rule_results: List[Dict[str, Any]] = [
        evaluate_rule_with_confidence(text, rule) for rule in rules
    ]
    summary = summarize_results(rule_results)
    file_hash = compute_document_hash(file_bytes)
    evidence_json = build_evidence_json(filename, file_hash, summary, rule_results)

    return summary, rule_results, evidence_json, file_hash