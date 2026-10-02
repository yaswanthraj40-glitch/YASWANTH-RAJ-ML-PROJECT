from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.schemas import PatientCreate, PatientUpdate, PatientResponse, PatientDetailResponse
from app.services.patient_service import PatientService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(p: PatientCreate):
    return PatientService.create_patient(p)

@router.get("", response_model=List[PatientResponse])
def get_patients(q: Optional[str] = Query(None, description="Search by name or patient code")):
    return PatientService.get_all_patients(query=q)

@router.get("/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(patient_id: int):
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")
    return patient

@router.put("/{patient_id}", response_model=PatientDetailResponse)
def update_patient(patient_id: int, p: PatientUpdate):
    updated = PatientService.update_patient(patient_id, p)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")
    return updated

@router.delete("/{patient_id}")
def delete_patient(patient_id: int):
    deleted = PatientService.delete_patient(patient_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")
    return {"message": "Patient deleted successfully", "id": patient_id}

@router.get("/{patient_id}/timeline")
def get_patient_timeline(patient_id: int):
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")
    timeline = AnalyticsService.get_patient_timeline(patient_id)
    return {"patient_id": patient_id, "name": patient["name"], "timeline": timeline}
