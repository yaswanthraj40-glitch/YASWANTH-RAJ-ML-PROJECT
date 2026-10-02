from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS
from app.database import init_db
from app.routers import patients, assessments, analytics

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables and indexes exist
    init_db()
    yield

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Sub-Routers
app.include_router(patients.router)
app.include_router(assessments.router)
app.include_router(analytics.router)

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "service": "Predictive Healthcare Assistant API"
    }

# Mount Frontend Static Assets and Serve Single Full-Stack Portal
if FRONTEND_DIR.exists():
    @app.get("/", tags=["UI Portal"], include_in_schema=False)
    def serve_frontend_ui():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/", tags=["System"])
    def root():
        return {
            "message": "Predictive Healthcare Assistant API is running",
            "version": APP_VERSION,
            "docs_url": "/docs",
            "health": "OK"
        }
