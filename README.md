# Predictive Healthcare Assistant – Early Disease Risk Assessment

A full-stack starter project with:
- Frontend: HTML, CSS, JavaScript
- Backend: Python FastAPI
- ML-style risk assessment engine
- SQLite database for assessment history
- REST API

## Run Application (Single Command & Single Link)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 🌟 Unified Single Link (Frontend UI + Backend API):
Open in your browser:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

- **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Population Analytics Summary**: [http://127.0.0.1:8000/api/analytics/summary](http://127.0.0.1:8000/api/analytics/summary)

## Run Automated Tests
```bash
cd backend
pytest -v
```

## Run Frontend
Open `frontend/index.html` in a browser.

If your browser blocks API requests from a local file, run:
```bash
cd frontend
python -m http.server 5500
```
Then open http://127.0.0.1:5500

## Key Backend Features
- **Modular Layered Architecture**: Routers, services, schemas, and database context managers separated cleanly.
- **Evidence-Calibrated Risk Engine**: Multi-condition stratification (Diabetes, Cardiovascular, Hypertension) with tiered severity and clinical explanations.
- **Population Analytics**: Aggregated risk distribution, biomarker averages, and patient count metrics at `/api/analytics/summary`.
- **Dataset Export**: One-click CSV export at `/api/export/assessments/csv`.
- **Longitudinal History & Timelines**: Patient vital progression tracking at `/api/patients/{id}/timeline`.

## Important
This project is an educational risk-assessment prototype. It does not diagnose disease or replace a qualified healthcare professional.
