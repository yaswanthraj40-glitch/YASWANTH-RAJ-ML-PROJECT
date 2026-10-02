from typing import Dict, Any, List
from app.models.schemas import Assessment

def clamp(val: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    return max(min_val, min(max_val, round(val, 1)))

def get_risk_tier(score: float) -> str:
    if score < 30.0:
        return "LOW"
    elif score < 60.0:
        return "MEDIUM"
    elif score < 85.0:
        return "HIGH"
    return "CRITICAL"

def predict_risks(a: Assessment) -> Dict[str, Any]:
    """
    Computes multi-dimensional risk scores (Diabetes, Cardiovascular, Hypertension)
    incorporating evidence-based clinical indicators, risk factors, category breakdowns,
    and tailored lifestyle/preventive recommendations.
    """
    # -------------------------------------------------------------
    # 1. Diabetes Risk Modeling (calibrated with ADA risk scoring)
    # -------------------------------------------------------------
    diabetes = 10.0
    diabetes_notes = []

    if a.age >= 65:
        diabetes += 18.0
        diabetes_notes.append("Age >= 65 significantly elevates insulin resistance vulnerability.")
    elif a.age >= 45:
        diabetes += 12.0
        diabetes_notes.append("Age 45-64 increases risk of metabolic changes.")

    if a.bmi >= 35.0:
        diabetes += 25.0
        diabetes_notes.append(f"Severe obesity (BMI {a.bmi}) is a primary driver of type 2 diabetes.")
    elif a.bmi >= 30.0:
        diabetes += 18.0
        diabetes_notes.append(f"Obesity class I (BMI {a.bmi}) impedes glycemic control.")
    elif a.bmi >= 25.0:
        diabetes += 10.0
        diabetes_notes.append(f"Overweight status (BMI {a.bmi}) adds moderate glycemic load.")

    if a.glucose >= 126.0:
        diabetes += 35.0
        diabetes_notes.append(f"Fasting glucose {a.glucose} mg/dL meets clinical diabetic threshold (>=126).")
    elif a.glucose >= 100.0:
        diabetes += 20.0
        diabetes_notes.append(f"Fasting glucose {a.glucose} mg/dL indicates impaired fasting glucose / pre-diabetes.")

    if a.activity == "low":
        diabetes += 8.0
        diabetes_notes.append("Sedentary lifestyle reduces peripheral glucose uptake.")
    elif a.activity == "high":
        diabetes -= 5.0

    if a.smoking == "yes":
        diabetes += 6.0
        diabetes_notes.append("Nicotine exposure promotes insulin resistance.")

    # -------------------------------------------------------------
    # 2. Cardiovascular Risk Modeling (Framingham & AHA indicators)
    # -------------------------------------------------------------
    heart = 8.0
    heart_notes = []

    if a.age >= 65:
        heart += 20.0
        heart_notes.append("Advanced age is an independent non-modifiable CVD risk factor.")
    elif a.age >= 45:
        heart += 14.0
        heart_notes.append("Age >= 45 is associated with progressive vascular stiffness.")

    if a.systolic_bp >= 160.0:
        heart += 28.0
        heart_notes.append(f"Stage 2 severe hypertension ({a.systolic_bp} mmHg) causes myocardial strain.")
    elif a.systolic_bp >= 140.0:
        heart += 18.0
        heart_notes.append(f"Hypertension ({a.systolic_bp} mmHg) increases cardiovascular workload.")
    elif a.systolic_bp >= 130.0:
        heart += 10.0
        heart_notes.append(f"Elevated systolic BP ({a.systolic_bp} mmHg).")

    if a.cholesterol >= 240.0:
        heart += 25.0
        heart_notes.append(f"High cholesterol ({a.cholesterol} mg/dL) accelerates atherogenesis.")
    elif a.cholesterol >= 200.0:
        heart += 14.0
        heart_notes.append(f"Borderline high cholesterol ({a.cholesterol} mg/dL).")

    if a.smoking == "yes":
        heart += 18.0
        heart_notes.append("Smoking damages endothelial lining and precipitates arterial plaque instability.")

    if a.heart_rate >= 100.0:
        heart += 10.0
        heart_notes.append(f"Tachycardia ({a.heart_rate} bpm at rest) signals sympathetic overactivity.")
    elif a.heart_rate < 50.0:
        heart += 4.0

    if a.bmi >= 30.0:
        heart += 8.0

    if a.activity == "low":
        heart += 7.0
        heart_notes.append("Low aerobic capacity is linked with increased coronary artery disease.")
    elif a.activity == "high":
        heart -= 6.0

    # -------------------------------------------------------------
    # 3. Hypertension Risk Modeling (ACC/AHA Guidelines)
    # -------------------------------------------------------------
    hypertension = 8.0
    hypertension_notes = []

    if a.systolic_bp >= 160.0:
        hypertension += 45.0
        hypertension_notes.append(f"Systolic pressure {a.systolic_bp} mmHg indicates severe stage 2 hypertension.")
    elif a.systolic_bp >= 140.0:
        hypertension += 32.0
        hypertension_notes.append(f"Systolic pressure {a.systolic_bp} mmHg indicates stage 1 hypertension.")
    elif a.systolic_bp >= 130.0:
        hypertension += 18.0
        hypertension_notes.append(f"Pre-hypertensive state ({a.systolic_bp} mmHg).")

    if a.age >= 60:
        hypertension += 15.0
    elif a.age >= 45:
        hypertension += 10.0

    if a.bmi >= 30.0:
        hypertension += 16.0
        hypertension_notes.append("High adiposity correlates strongly with increased systemic vascular resistance.")
    elif a.bmi >= 25.0:
        hypertension += 8.0

    if a.smoking == "yes":
        hypertension += 8.0
        hypertension_notes.append("Acute vasoconstriction induced by tobacco.")

    if a.activity == "low":
        hypertension += 7.0
    elif a.activity == "high":
        hypertension -= 5.0

    # -------------------------------------------------------------
    # Normalization & Aggregate Tiers
    # -------------------------------------------------------------
    diabetes_clamped = clamp(diabetes)
    heart_clamped = clamp(heart)
    hypertension_clamped = clamp(hypertension)

    avg_score = (diabetes_clamped + heart_clamped + hypertension_clamped) / 3.0
    
    if avg_score < 30.0:
        overall_risk = "LOW"
    elif avg_score < 60.0:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "HIGH"

    # Specific clinical flags
    factors: List[str] = []
    if a.glucose >= 126.0:
        factors.append(f"Diagnostic-level hyperglycemia (Glucose {a.glucose} mg/dL ≥ 126)")
    elif a.glucose >= 100.0:
        factors.append(f"Impaired fasting glucose (Glucose {a.glucose} mg/dL ≥ 100)")

    if a.systolic_bp >= 140.0:
        factors.append(f"Stage 1/2 Hypertension (Systolic BP {a.systolic_bp} mmHg ≥ 140)")
    elif a.systolic_bp >= 130.0:
        factors.append(f"Pre-hypertension / elevated pressure (Systolic BP {a.systolic_bp} mmHg)")

    if a.bmi >= 30.0:
        factors.append(f"Clinical Obesity (BMI {a.bmi} ≥ 30)")
    elif a.bmi >= 25.0:
        factors.append(f"Overweight classification (BMI {a.bmi} ≥ 25)")

    if a.cholesterol >= 240.0:
        factors.append(f"High Hypercholesterolemia (Total Chol {a.cholesterol} mg/dL ≥ 240)")
    elif a.cholesterol >= 200.0:
        factors.append(f"Borderline elevated cholesterol (Total Chol {a.cholesterol} mg/dL ≥ 200)")

    if a.smoking.lower() in ("yes", "true", "1"):
        factors.append("Active tobacco smoking / nicotine use")

    if a.activity.lower() == "low":
        factors.append("Sedentary physical activity profile")

    if a.heart_rate >= 100.0:
        factors.append(f"Resting Tachycardia ({a.heart_rate} bpm ≥ 100)")

    if not factors:
        factors.append("No major acute clinical risk factors detected in this screening")

    # Recommendations
    recommendations: List[str] = []
    if diabetes_clamped >= 50.0 or a.glucose >= 100.0:
        recommendations.append("Obtain HbA1c testing and consider oral glucose tolerance evaluation.")
        recommendations.append("Adopt low-glycemic Mediterranean dietary patterns rich in high fiber.")
    
    if heart_clamped >= 50.0 or a.cholesterol >= 200.0:
        recommendations.append("Request a complete fasting lipid panel (LDL-C, HDL-C, Triglycerides) and cardiovascular screening.")
        recommendations.append("Limit saturated and trans-fat intake; consider omega-3 supplementation under medical guidance.")

    if hypertension_clamped >= 50.0 or a.systolic_bp >= 130.0:
        recommendations.append("Implement dietary sodium restriction (< 2,000 mg/day) following DASH diet guidelines.")
        recommendations.append("Keep a daily morning/evening blood pressure log for clinical review.")

    if a.smoking.lower() in ("yes", "true", "1"):
        recommendations.append("Engage in a structured smoking cessation program (nicotine replacement / behavioral counseling).")

    if a.activity.lower() == "low":
        recommendations.append("Gradually build towards 150 minutes of moderate aerobic exercise (e.g. brisk walking) weekly.")

    # Universal baseline recommendations
    recommendations.append("Maintain routine preventive health monitoring with a licensed healthcare practitioner.")

    # Category breakdown object
    category_breakdowns = {
        "diabetes": {
            "risk_percentage": diabetes_clamped,
            "category": get_risk_tier(diabetes_clamped),
            "notes": diabetes_notes or ["Glycemic parameters within normal physiological screening ranges."]
        },
        "heart": {
            "risk_percentage": heart_clamped,
            "category": get_risk_tier(heart_clamped),
            "notes": heart_notes or ["Cardiovascular parameters within standard screening thresholds."]
        },
        "hypertension": {
            "risk_percentage": hypertension_clamped,
            "category": get_risk_tier(hypertension_clamped),
            "notes": hypertension_notes or ["Hemodynamic blood pressure within healthy parameters."]
        }
    }

    vitals_summary = {
        "bmi_status": "Obese" if a.bmi >= 30 else "Overweight" if a.bmi >= 25 else "Normal" if a.bmi >= 18.5 else "Underweight",
        "bp_status": "Stage 2" if a.systolic_bp >= 160 else "Stage 1" if a.systolic_bp >= 140 else "Elevated" if a.systolic_bp >= 130 else "Normal",
        "glucose_status": "Diabetic Range" if a.glucose >= 126 else "Pre-diabetic Range" if a.glucose >= 100 else "Normal",
        "cholesterol_status": "High" if a.cholesterol >= 240 else "Borderline" if a.cholesterol >= 200 else "Desirable"
    }

    return {
        "diabetes_risk": diabetes_clamped,
        "heart_risk": heart_clamped,
        "hypertension_risk": hypertension_clamped,
        "overall_risk": overall_risk,
        "risk_factors": factors,
        "recommendations": recommendations,
        "category_breakdowns": category_breakdowns,
        "vitals_summary": vitals_summary
    }
