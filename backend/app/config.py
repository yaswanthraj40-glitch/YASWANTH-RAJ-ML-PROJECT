import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = os.getenv("HEALTHCARE_DB_PATH", str(BASE_DIR / "healthcare.db"))
APP_VERSION = "2.5.0"
APP_TITLE = "Predictive Healthcare Assistant API"
APP_DESCRIPTION = "Evidence-informed Clinical Risk Stratification & Longitudinal Patient Management System"

CORS_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "*"
]
