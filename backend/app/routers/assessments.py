from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.schemas import Assessment, PredictionResult, AssessmentRecord
from app.services.assessment_service import AssessmentService
from app.services.predictor import predict_risks

router = APIRouter(tags=["Assessments & Risk Prediction"])

@router.post("/api/predict", response_model=PredictionResult)
def make_prediction(a: Assessment):
    """
    Run clinical risk calculation engine and store the assessment record in the database.
    """
    return AssessmentService.create_assessment(a)

@router.post("/api/evaluate-only")
def evaluate_without_saving(a: Assessment):
    """
    Simulate risk metrics without writing to persistent storage.
    """
    return predict_risks(a)

@router.get("/api/history", response_model=List[AssessmentRecord])
def get_history(
    patient_id: Optional[int] = Query(None, description="Filter history by patient ID"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return")
):
    """
    Retrieve historical clinical assessments.
    """
    return AssessmentService.get_history(patient_id=patient_id, search=search, limit=limit)

@router.get("/api/assessments/{assessment_id}", response_model=AssessmentRecord)
def get_assessment(assessment_id: int):
    record = AssessmentService.get_assessment_by_id(assessment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Assessment #{assessment_id} not found.")
    return record
