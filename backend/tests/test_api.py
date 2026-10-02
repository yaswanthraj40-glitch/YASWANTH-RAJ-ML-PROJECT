import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    test_db = os.path.join(temp_dir, "test_healthcare.db")
    monkeypatch.setenv("HEALTHCARE_DB_PATH", test_db)
    init_db(test_db)
    
    import app.config as config
    monkeypatch.setattr(config, "DB_FILE", test_db)
    
    yield test_db

@pytest.fixture
def client():
    return TestClient(app)

def test_root_and_health(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text or "Predictive Healthcare" in res.text

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

def test_patient_crud_flow(client):
    # 1. Create Patient
    payload = {
        "name": "Jane Doe",
        "age": 42,
        "gender": "Female",
        "contact": "+1-555-0199",
        "blood_group": "O+",
        "medical_history": "Mild asthma"
    }
    create_res = client.post("/api/patients", json=payload)
    assert create_res.status_code == 201
    patient = create_res.json()
    assert patient["name"] == "Jane Doe"
    assert "PAT-" in patient["patient_code"]
    patient_id = patient["id"]

    # 2. Get All Patients
    get_res = client.get("/api/patients")
    assert get_res.status_code == 200
    patients = get_res.json()
    assert len(patients) == 1
    assert patients[0]["id"] == patient_id

    # 3. Get Patient Detail
    detail_res = client.get(f"/api/patients/{patient_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["medical_history"] == "Mild asthma"

    # 4. Update Patient
    update_res = client.put(f"/api/patients/{patient_id}", json={"medical_history": "Asthma controlled"})
    assert update_res.status_code == 200
    assert update_res.json()["medical_history"] == "Asthma controlled"

    # 5. Delete Patient
    del_res = client.delete(f"/api/patients/{patient_id}")
    assert del_res.status_code == 200
    
    # 6. Verify 404 after deletion
    not_found_res = client.get(f"/api/patients/{patient_id}")
    assert not_found_res.status_code == 404

def test_prediction_and_history(client):
    # Register a patient
    p_res = client.post("/api/patients", json={
        "name": "Robert Smith",
        "age": 55,
        "gender": "Male",
        "blood_group": "A-"
    })
    patient = p_res.json()

    # Make assessment
    assessment_payload = {
        "patient_id": patient["id"],
        "patient_code": patient["patient_code"],
        "name": patient["name"],
        "age": patient["age"],
        "gender": patient["gender"],
        "bmi": 28.5,
        "systolic_bp": 142.0,
        "glucose": 110.0,
        "cholesterol": 215.0,
        "heart_rate": 78.0,
        "smoking": "no",
        "activity": "medium"
    }
    pred_res = client.post("/api/predict", json=assessment_payload)
    assert pred_res.status_code == 200
    result = pred_res.json()
    assert result["patient_id"] == patient["id"]
    assert "diabetes_risk" in result
    assert "hypertension_risk" in result
    assert "category_breakdowns" in result

    # Check history endpoint
    hist_res = client.get(f"/api/history?patient_id={patient['id']}")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 1
    assert history[0]["name"] == "Robert Smith"

def test_analytics_and_csv_export(client):
    # Perform an assessment
    client.post("/api/predict", json={
        "name": "Alice Wonderland",
        "age": 30,
        "gender": "Female",
        "bmi": 22.0,
        "systolic_bp": 118.0,
        "glucose": 90.0,
        "cholesterol": 170.0,
        "heart_rate": 70.0,
        "smoking": "no",
        "activity": "high"
    })

    # Test summary analytics
    summary_res = client.get("/api/analytics/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_assessments"] >= 1
    assert "risk_distribution" in summary
    assert "average_vitals" in summary

    # Test CSV export
    csv_res = client.get("/api/export/assessments/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Assessment ID" in csv_res.text
    assert "Alice Wonderland" in csv_res.text
