from fastapi import APIRouter, Response
from app.models.schemas import AnalyticsSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api", tags=["Analytics & Population Health"])

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary():
    """
    Returns population-level clinical analytics, risk category counts, average biomarkers, and latest screenings.
    """
    return AnalyticsService.get_summary()

@router.get("/export/assessments/csv")
def export_assessments_csv():
    """
    Exports all assessments as a downloadable CSV dataset.
    """
    csv_content = AnalyticsService.generate_assessments_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=clinical_assessments_export.csv"
        }
    )
