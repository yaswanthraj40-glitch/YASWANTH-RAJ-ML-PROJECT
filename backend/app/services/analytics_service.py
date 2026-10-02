import io
import csv
from typing import Dict, Any, List, Optional
from app.database import get_db

class AnalyticsService:
    @staticmethod
    def get_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
        with get_db(db_path) if db_path else get_db() as conn:
            total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            total_assessments = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]

            # Risk counts
            risk_rows = conn.execute("""
                SELECT overall_risk, COUNT(*) as count 
                FROM assessments 
                GROUP BY overall_risk
            """).fetchall()
            
            risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
            for r in risk_rows:
                risk_distribution[r["overall_risk"]] = r["count"]

            risk_percentages = {}
            for k, count in risk_distribution.items():
                risk_percentages[k] = round((count / total_assessments * 100.0), 1) if total_assessments > 0 else 0.0

            # Average vitals
            avg_row = conn.execute("""
                SELECT 
                    AVG(bmi) as avg_bmi,
                    AVG(systolic_bp) as avg_bp,
                    AVG(glucose) as avg_glucose,
                    AVG(cholesterol) as avg_cholesterol,
                    AVG(heart_rate) as avg_hr,
                    AVG(diabetes_risk) as avg_diabetes,
                    AVG(heart_risk) as avg_heart,
                    AVG(hypertension_risk) as avg_hypertension
                FROM assessments
            """).fetchone()

            average_vitals = {
                "bmi": round(avg_row["avg_bmi"] or 0, 1),
                "systolic_bp": round(avg_row["avg_bp"] or 0, 1),
                "glucose": round(avg_row["avg_glucose"] or 0, 1),
                "cholesterol": round(avg_row["avg_cholesterol"] or 0, 1),
                "heart_rate": round(avg_row["avg_hr"] or 0, 1),
                "diabetes_risk": round(avg_row["avg_diabetes"] or 0, 1),
                "heart_risk": round(avg_row["avg_heart"] or 0, 1),
                "hypertension_risk": round(avg_row["avg_hypertension"] or 0, 1),
            }

            high_risk_patients = conn.execute("""
                SELECT COUNT(DISTINCT patient_id) 
                FROM assessments 
                WHERE overall_risk = 'HIGH' AND patient_id IS NOT NULL
            """).fetchone()[0]

            latest_rows = conn.execute("""
                SELECT * FROM assessments ORDER BY id DESC LIMIT 5
            """).fetchall()

            return {
                "total_patients": total_patients,
                "total_assessments": total_assessments,
                "risk_distribution": risk_distribution,
                "risk_percentages": risk_percentages,
                "average_vitals": average_vitals,
                "high_risk_patients_count": high_risk_patients,
                "latest_assessments": [dict(r) for r in latest_rows]
            }

    @staticmethod
    def get_patient_timeline(patient_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            rows = conn.execute("""
                SELECT id, created_at, systolic_bp, glucose, cholesterol, bmi, heart_rate,
                       diabetes_risk, heart_risk, hypertension_risk, overall_risk
                FROM assessments
                WHERE patient_id = ?
                ORDER BY id ASC
            """, (patient_id,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def generate_assessments_csv(db_path: Optional[str] = None) -> str:
        with get_db(db_path) if db_path else get_db() as conn:
            rows = conn.execute("""
                SELECT id, patient_id, patient_code, name, age, gender, bmi, systolic_bp,
                       glucose, cholesterol, heart_rate, smoking, activity,
                       diabetes_risk, heart_risk, hypertension_risk, overall_risk, created_at
                FROM assessments
                ORDER BY id DESC
            """).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            
            headers = [
                "Assessment ID", "Patient ID", "Patient Code", "Name", "Age", "Gender",
                "BMI (kg/m2)", "Systolic BP (mmHg)", "Glucose (mg/dL)", "Cholesterol (mg/dL)",
                "Heart Rate (bpm)", "Smoking", "Physical Activity", "Diabetes Risk (%)",
                "Cardiovascular Risk (%)", "Hypertension Risk (%)", "Overall Risk", "Created At"
            ]
            writer.writerow(headers)

            for r in rows:
                writer.writerow([
                    r["id"], r["patient_id"] or "", r["patient_code"] or "", r["name"],
                    r["age"], r["gender"], r["bmi"], r["systolic_bp"], r["glucose"],
                    r["cholesterol"], r["heart_rate"], r["smoking"], r["activity"],
                    r["diabetes_risk"], r["heart_risk"], r["hypertension_risk"],
                    r["overall_risk"], r["created_at"]
                ])

            return output.getvalue()
