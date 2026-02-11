from backend.utils.schema_validator import validate_schema


def test_false_unification_schema_valid():
    payload = {
        "detected": False,
        "risk_score": 0.0,
        "confidence": 0.8,
        "risk_level": "BAJO",
        "issues": [],
        "entity_type": "cooperativa",
        "summary": "OK",
        "total_issues": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0
    }
    ok, err = validate_schema(payload, "false_unification")
    assert ok, err


def test_false_unification_schema_invalid():
    payload = {"detected": True}  # incompleto
    ok, err = validate_schema(payload, "false_unification")
    assert not ok
