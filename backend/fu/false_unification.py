from __future__ import annotations

from typing import Dict, List

from backend.fu.false_unification_rules import (
    ENTITY_PROFILES,
    INCONSISTENCY_DETECTORS,
    SFC_REFERENCES,
)
from backend.utils.schema_validator import validate_or_raise


class FalseUnificationDetector:
    SEVERITY_WEIGHTS = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.2}

    RISK_THRESHOLDS = {
        "BAJO": (0.0, 0.25),
        "MEDIO": (0.25, 0.55),
        "ALTO": (0.55, 0.80),
        "CRITICO": (0.80, 1.01),
    }

    def analyze(self, text: str, entity_type: str) -> Dict:
        if not text or len(text.strip()) == 0:
            return self._empty_text_response(entity_type)

        if entity_type not in ENTITY_PROFILES:
            return self._no_profile_response(entity_type)

        profile = ENTITY_PROFILES[entity_type]
        text_lower = text.lower()

        issues: List[Dict] = []
        issues.extend(self._detect_forbidden_terms(text, text_lower, profile))
        issues.extend(self._detect_missing_sections(text_lower, profile))
        issues.extend(self._detect_inconsistencies(text_lower))

        risk_score = self._calculate_risk_score_deterministic(issues)
        risk_level = self._get_risk_level(risk_score)

        result = {
            "detected": len(issues) > 0,
            "risk_score": risk_score,
            "confidence": self._calculate_confidence(text, issues),
            "risk_level": risk_level,
            "issues": sorted(
                issues,
                key=lambda x: self.SEVERITY_WEIGHTS.get(x.get("severity", "LOW"), 0.2),
                reverse=True,
            ),
            "entity_type": entity_type,
            "summary": self._build_summary(entity_type, risk_level, issues),
            "total_issues": len(issues),
            "high_severity": sum(1 for i in issues if i.get("severity") == "HIGH"),
            "medium_severity": sum(1 for i in issues if i.get("severity") == "MEDIUM"),
            "low_severity": sum(1 for i in issues if i.get("severity") == "LOW"),
        }

        validate_or_raise(result, "false_unification")
        return result

    def _detect_forbidden_terms(self, text: str, text_lower: str, profile: Dict) -> List[Dict]:
        issues = []
        for rule in profile.get("forbidden_terms", []):
            for term in rule.get("terms", []):
                if term.lower() in text_lower:
                    idx = text_lower.find(term.lower())
                    start = max(0, idx - 160)
                    end = min(len(text), idx + 160)
                    evidence = f"...{text[start:end].strip()}..."

                    sfc_ref_id = rule.get("sfc_ref_id")
                    issues.append(
                        {
                            "id": rule["id"],
                            "type": "FORBIDDEN_TERM",
                            "severity": rule["severity"],
                            "title": rule["title"],
                            "evidence": evidence,
                            "recommendation": rule["recommendation"],
                            "sfc_ref_id": sfc_ref_id,
                            "sfc_ref_text": SFC_REFERENCES.get(sfc_ref_id) if sfc_ref_id else None,
                        }
                    )
                    break
        return issues

    def _detect_missing_sections(self, text_lower: str, profile: Dict) -> List[Dict]:
        issues = []
        for req in profile.get("required_sections", []):
            found = any(kw.lower() in text_lower for kw in req.get("keywords", []))
            if not found:
                sfc_ref_id = req.get("sfc_ref_id")
                issues.append(
                    {
                        "id": req["id"],
                        "type": "MISSING_SECTION",
                        "severity": req["severity"],
                        "title": f"Sección requerida ausente: {req['name']}",
                        "evidence": None,
                        "recommendation": req["recommendation"],
                        "sfc_ref_id": sfc_ref_id,
                        "sfc_ref_text": SFC_REFERENCES.get(sfc_ref_id) if sfc_ref_id else None,
                    }
                )
        return issues

    def _detect_inconsistencies(self, text_lower: str) -> List[Dict]:
        issues = []
        for det in INCONSISTENCY_DETECTORS:
            has_first = any(t in text_lower for t in det.get("check_has", []))
            has_second = any(t in text_lower for t in det.get("check_also_has", []))
            if has_first and has_second:
                sfc_ref_id = det.get("sfc_ref_id")
                issues.append(
                    {
                        "id": det["id"],
                        "type": "INCONSISTENCY",
                        "severity": det["severity"],
                        "title": det["name"],
                        "evidence": None,
                        "recommendation": det["recommendation"],
                        "sfc_ref_id": sfc_ref_id,
                        "sfc_ref_text": SFC_REFERENCES.get(sfc_ref_id) if sfc_ref_id else None,
                    }
                )
        return issues

    def _calculate_risk_score_deterministic(self, issues: List[Dict]) -> float:
        if not issues:
            return 0.0
        weighted_sum = sum(self.SEVERITY_WEIGHTS.get(i.get("severity", "LOW"), 0.2) for i in issues)
        max_possible = 10.0
        score = min(0.98, weighted_sum / max_possible)
        return round(score, 2)

    def _get_risk_level(self, score: float) -> str:
        for level, (low, high) in self.RISK_THRESHOLDS.items():
            if low <= score < high:
                return level
        return "CRITICO"

    def _calculate_confidence(self, text: str, issues: List[Dict]) -> float:
        if len(text) < 500:
            base = 0.55
        elif len(text) > 5000:
            base = 0.85
        else:
            base = 0.75

        with_evidence = sum(1 for i in issues if i.get("evidence"))
        if issues and with_evidence / len(issues) > 0.6:
            base += 0.1

        return round(min(0.95, base), 2)

    def _build_summary(self, entity_type: str, risk_level: str, issues: List[Dict]) -> str:
        if not issues:
            return f"No se detectaron inconsistencias de false unification para {entity_type}."
        high = sum(1 for i in issues if i.get("severity") == "HIGH")
        med = sum(1 for i in issues if i.get("severity") == "MEDIUM")
        return (
            f"Nivel de riesgo {risk_level}: {len(issues)} hallazgos "
            f"({high} altos, {med} medios). Ajustar el documento al perfil de {entity_type}."
        )

    def _no_profile_response(self, entity_type: str) -> Dict:
        return {
            "detected": False,
            "risk_score": 0.0,
            "confidence": 0.0,
            "risk_level": "BAJO",
            "issues": [],
            "entity_type": entity_type,
            "summary": f"Perfil no disponible para '{entity_type}'. Análisis no realizado.",
            "total_issues": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
        }

    def _empty_text_response(self, entity_type: str) -> Dict:
        return {
            "detected": False,
            "risk_score": 0.0,
            "confidence": 0.0,
            "risk_level": "BAJO",
            "issues": [],
            "entity_type": entity_type,
            "summary": "Texto vacío o no procesable. No se pudo analizar false unification.",
            "total_issues": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
        }
