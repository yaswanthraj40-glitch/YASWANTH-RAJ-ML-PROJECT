from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.schemas import Assessment
from app.services.predictor import predict_risks

class AssessmentService:
    @staticmethod
    def create_assessment(a: Assessment, db_path: Optional[str] = None) -> Dict[str, Any]:
        result = predict_risks(a)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        patient_id = a.patient_id
        patient_code = a.patient_code

        with get_db(db_path) if db_path else get_db() as conn:
            cursor = conn.cursor()

            # Auto-link by exact name if patient_id is not provided
            if not patient_id:
                p_row = conn.execute(
                    "SELECT id, patient_code FROM patients WHERE name = ? COLLATE NOCASE LIMIT 1",
                    (a.name.strip(),)
                ).fetchone()
                if p_row:
                    patient_id = p_row["id"]
                    patient_code = p_row["patient_code"]

            cursor.execute("""
                INSERT INTO assessments
                (patient_id, patient_code, name, age, gender, bmi, systolic_bp, glucose, cholesterol, heart_rate,
                 smoking, activity, diabetes_risk, heart_risk, hypertension_risk, overall_risk, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                patient_code,
                a.name.strip(),
                a.age,
                a.gender,
                a.bmi,
                a.systolic_bp,
                a.glucose,
                a.cholesterol,
                a.heart_rate,
                a.smoking,
                a.activity,
                result["diabetes_risk"],
                result["heart_risk"],
                result["hypertension_risk"],
                result["overall_risk"],
                created_at
            ))

            assessment_id = cursor.lastrowid

        return {
            "id": assessment_id,
            "patient_id": patient_id,
            "patient_code": patient_code,
            "name": a.name.strip(),
            "age": a.age,
            "gender": a.gender,
            "bmi": a.bmi,
            "systolic_bp": a.systolic_bp,
            "glucose": a.glucose,
            "cholesterol": a.cholesterol,
            "heart_rate": a.heart_rate,
            "smoking": a.smoking,
            "activity": a.activity,
            "diabetes_risk": result["diabetes_risk"],
            "heart_risk": result["heart_risk"],
            "hypertension_risk": result["hypertension_risk"],
            "overall_risk": result["overall_risk"],
            "risk_factors": result["risk_factors"],
            "recommendations": result["recommendations"],
            "category_breakdowns": result.get("category_breakdowns"),
            "vitals_summary": result.get("vitals_summary"),
            "created_at": created_at
        }

    @staticmethod
    def get_history(
        patient_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        db_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            query = "SELECT * FROM assessments WHERE 1=1"
            params = []

            if patient_id:
                query += " AND patient_id = ?"
                params.append(patient_id)

            if search:
                query += " AND (name LIKE ? OR patient_code LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term])

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_assessment_by_id(assessment_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
            return dict(row) if row else None
