import pytest
from app.models.schemas import Assessment
from app.services.predictor import predict_risks, clamp

def test_clamp_utility():
    assert clamp(110.5) == 100.0
    assert clamp(-5.2) == 0.0
    assert clamp(45.67) == 45.7

def test_low_risk_healthy_profile():
    assessment = Assessment(
        name="Healthy Individual",
        age=25,
        gender="Female",
        bmi=21.5,
        systolic_bp=115.0,
        glucose=85.0,
        cholesterol=160.0,
        heart_rate=65.0,
        smoking="no",
        activity="high"
    )
    result = predict_risks(assessment)
    assert result["overall_risk"] == "LOW"
    assert result["diabetes_risk"] < 30.0
    assert result["heart_risk"] < 30.0
    assert result["hypertension_risk"] < 30.0
    assert len(result["risk_factors"]) > 0
    assert len(result["recommendations"]) > 0

def test_high_risk_diabetic_cardio_profile():
    assessment = Assessment(
        name="High Risk Patient",
        age=68,
        gender="Male",
        bmi=36.2,
        systolic_bp=165.0,
        glucose=180.0,
        cholesterol=260.0,
        heart_rate=105.0,
        smoking="yes",
        activity="low"
    )
    result = predict_risks(assessment)
    assert result["overall_risk"] == "HIGH"
    assert result["diabetes_risk"] >= 60.0
    assert result["heart_risk"] >= 60.0
    assert result["hypertension_risk"] >= 60.0
    assert any("Hyperglycemia" in f or "glucose" in f.lower() for f in result["risk_factors"])
    assert any("Hypertension" in f or "systolic" in f.lower() for f in result["risk_factors"])
    assert "category_breakdowns" in result
    assert result["category_breakdowns"]["diabetes"]["category"] in ["HIGH", "CRITICAL"]
