import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.form_routes import router as form_router


app = FastAPI(
    title="FormSathi API",
    description="Backend services for OCR, AI field detection, translation, and PDF generation.",
    version="1.0.0",
)

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.generated_pdfs_dir, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(form_router)
app.mount("/generated_pdfs", StaticFiles(directory=settings.generated_pdfs_dir), name="generated_pdfs")


@app.get("/")
def health_check() -> dict:
    return {"status": "ok", "service": "FormSathi API"}
