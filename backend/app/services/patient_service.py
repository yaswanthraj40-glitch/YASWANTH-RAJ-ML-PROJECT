from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.schemas import PatientCreate, PatientUpdate

class PatientService:
    @staticmethod
    def create_patient(p: PatientCreate, db_path: Optional[str] = None) -> Dict[str, Any]:
        with get_db(db_path) if db_path else get_db() as conn:
            cursor = conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("SELECT COUNT(*) FROM patients")
            count = cursor.fetchone()[0] + 1
            patient_code = f"PAT-{count:04d}"

            # Ensure uniqueness if PAT-XXXX already exists
            cursor.execute("SELECT id FROM patients WHERE patient_code = ?", (patient_code,))
            if cursor.fetchone():
                patient_code = f"PAT-{int(datetime.now().timestamp()) % 100000:05d}"

            cursor.execute("""
                INSERT INTO patients (patient_code, name, age, gender, contact, blood_group, medical_history, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_code,
                p.name.strip(),
                p.age,
                p.gender,
                (p.contact or "").strip(),
                p.blood_group or "Unknown",
                (p.medical_history or "").strip(),
                created_at
            ))
            
            patient_id = cursor.lastrowid
            
            return {
                "id": patient_id,
                "patient_code": patient_code,
                "name": p.name.strip(),
                "age": p.age,
                "gender": p.gender,
                "contact": p.contact or "",
                "blood_group": p.blood_group or "Unknown",
                "medical_history": p.medical_history or "",
                "created_at": created_at,
                "assessment_count": 0,
                "latest_risk": None,
                "latest_assessment_date": None
            }

    @staticmethod
    def get_all_patients(query: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            base_sql = """
                SELECT p.*, 
                       (SELECT COUNT(*) FROM assessments a WHERE a.patient_id = p.id OR a.name = p.name COLLATE NOCASE) as assessment_count,
                       (SELECT a.overall_risk FROM assessments a WHERE a.patient_id = p.id OR a.name = p.name COLLATE NOCASE ORDER BY a.id DESC LIMIT 1) as latest_risk,
                       (SELECT a.created_at FROM assessments a WHERE a.patient_id = p.id OR a.name = p.name COLLATE NOCASE ORDER BY a.id DESC LIMIT 1) as latest_assessment_date
                FROM patients p 
            """
            params = []
            if query:
                base_sql += " WHERE p.name LIKE ? OR p.patient_code LIKE ? "
                search_term = f"%{query}%"
                params = [search_term, search_term]

            base_sql += " ORDER BY p.id DESC"
            rows = conn.execute(base_sql, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_patient_by_id(patient_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            p_row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not p_row:
                return None
            
            p_dict = dict(p_row)
            
            assessments = conn.execute("""
                SELECT * FROM assessments 
                WHERE patient_id = ? OR name = ? COLLATE NOCASE
                ORDER BY id DESC
            """, (patient_id, p_dict["name"])).fetchall()
            
            p_dict["assessments"] = [dict(a) for a in assessments]
            p_dict["assessment_count"] = len(p_dict["assessments"])
            if p_dict["assessments"]:
                p_dict["latest_risk"] = p_dict["assessments"][0].get("overall_risk")
                p_dict["latest_assessment_date"] = p_dict["assessments"][0].get("created_at")
            else:
                p_dict["latest_risk"] = None
                p_dict["latest_assessment_date"] = None
                
            return p_dict

    @staticmethod
    def update_patient(patient_id: int, p: PatientUpdate, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with get_db(db_path) if db_path else get_db() as conn:
            existing = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not existing:
                return None
            
            fields = []
            values = []
            for k, v in p.model_dump(exclude_unset=True).items():
                if v is not None:
                    fields.append(f"{k} = ?")
                    values.append(v)
            
            if fields:
                values.append(patient_id)
                conn.execute(f"UPDATE patients SET {', '.join(fields)} WHERE id = ?", tuple(values))
                conn.commit()
                
        return PatientService.get_patient_by_id(patient_id, db_path)

    @staticmethod
    def delete_patient(patient_id: int, db_path: Optional[str] = None) -> bool:
        with get_db(db_path) if db_path else get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            if cursor.rowcount == 0:
                return False
            cursor.execute("DELETE FROM assessments WHERE patient_id = ?", (patient_id,))
            return True
