from backend.fu.false_unification import FalseUnificationDetector


def test_cooperativa_detects_oficial_principal():
    det = FalseUnificationDetector()
    text = "Se designa un Oficial Principal SARLAFT y un Oficial Suplente."
    result = det.analyze(text, "cooperativa")
    assert result["detected"] is True
    assert result["high_severity"] >= 1


def test_cooperativa_detects_corresponsalia():
    det = FalseUnificationDetector()
    text = "La entidad mantiene red de corresponsalía bancaria internacional."
    result = det.analyze(text, "cooperativa")
    ids = [i["id"] for i in result["issues"]]
    assert "FU-COOP-002" in ids


def test_risk_score_is_deterministic():
    det = FalseUnificationDetector()
    text = "Oficial Principal SARLAFT corresponsalía bancaria casa matriz."
    r1 = det.analyze(text, "cooperativa")
    r2 = det.analyze(text, "cooperativa")
    assert r1["risk_score"] == r2["risk_score"]
