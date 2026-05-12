"""
FastAPI application entry point.
Run: uvicorn main:app --reload --port 8000
"""
import sys
from pathlib import Path

# Make backend/ the root so imports work
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.redact import router as redact_router

app = FastAPI(
    title="AI PII Redactor",
    description="Upload CSV / JSON / TXT / Image / PDF — receive a PII-redacted file.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(redact_router, prefix="/api")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve the frontend at /
frontend_dir = Path(__file__).parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
