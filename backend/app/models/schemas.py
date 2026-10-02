from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Patient full legal name")
    age: int = Field(..., ge=1, le=120, description="Patient age in years")
    gender: str = Field(..., description="Gender (Male, Female, Other)")
    contact: Optional[str] = Field(default="", description="Contact phone or email")
    blood_group: Optional[str] = Field(default="Unknown", description="Blood group (e.g. A+, O-, etc.)")
    medical_history: Optional[str] = Field(default="", description="Relevant pre-existing conditions and notes")

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    contact: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: Optional[str] = None
    name: str
    age: int
    gender: str
    contact: Optional[str] = ""
    blood_group: Optional[str] = "Unknown"
    medical_history: Optional[str] = ""
    created_at: str
    assessment_count: Optional[int] = 0
    latest_risk: Optional[str] = None
    latest_assessment_date: Optional[str] = None

class Assessment(BaseModel):
    patient_id: Optional[int] = Field(default=None, description="Optional link to registered patient ID")
    patient_code: Optional[str] = Field(default=None, description="Optional registered patient code")
    name: str = Field(..., min_length=1, max_length=100, description="Subject name")
    age: int = Field(..., ge=1, le=120, description="Age in years")
    gender: str = Field(..., description="Gender")
    bmi: float = Field(..., ge=10.0, le=80.0, description="Body Mass Index (kg/m²)")
    systolic_bp: float = Field(..., ge=60.0, le=260.0, description="Systolic Blood Pressure (mmHg)")
    glucose: float = Field(..., ge=40.0, le=500.0, description="Fasting/Random Glucose (mg/dL)")
    cholesterol: float = Field(..., ge=80.0, le=500.0, description="Total Serum Cholesterol (mg/dL)")
    heart_rate: float = Field(..., ge=30.0, le=220.0, description="Resting Heart Rate (bpm)")
    smoking: str = Field(..., description="Smoking status ('yes' or 'no')")
    activity: str = Field(..., description="Physical activity level ('low', 'medium', 'high')")

class ClinicalCategoryBreakdown(BaseModel):
    risk_percentage: float
    category: str
    notes: List[str]

class PredictionResult(BaseModel):
    id: Optional[int] = None
    patient_id: Optional[int] = None
    patient_code: Optional[str] = None
    name: str
    age: int
    gender: str
    bmi: float
    systolic_bp: float
    glucose: float
    cholesterol: float
    heart_rate: float
    smoking: str
    activity: str
    diabetes_risk: float
    heart_risk: float
    hypertension_risk: float
    overall_risk: str
    risk_factors: List[str]
    recommendations: List[str]
    created_at: Optional[str] = None
    category_breakdowns: Optional[Dict[str, ClinicalCategoryBreakdown]] = None
    vitals_summary: Optional[Dict[str, Any]] = None

class AssessmentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: Optional[int] = None
    patient_code: Optional[str] = None
    name: str
    age: int
    gender: str
    bmi: float
    systolic_bp: float
    glucose: float
    cholesterol: float
    heart_rate: float
    smoking: str
    activity: str
    diabetes_risk: float
    heart_risk: float
    hypertension_risk: float
    overall_risk: str
    created_at: str

class PatientDetailResponse(PatientResponse):
    assessments: List[AssessmentRecord] = []

class AnalyticsSummary(BaseModel):
    total_patients: int
    total_assessments: int
    risk_distribution: Dict[str, int]
    risk_percentages: Dict[str, float]
    average_vitals: Dict[str, float]
    high_risk_patients_count: int
    latest_assessments: List[AssessmentRecord]
