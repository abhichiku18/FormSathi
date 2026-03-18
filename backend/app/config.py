import os
import tempfile
from typing import List

from dotenv import load_dotenv


BASE_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME_DIR = os.path.normpath(os.path.join(tempfile.gettempdir(), "formsathi_runtime"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)


class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    upload_dir: str = os.path.normpath(os.path.join(RUNTIME_DIR, "uploads"))
    generated_pdfs_dir: str = os.path.normpath(os.path.join(RUNTIME_DIR, "generated_pdfs"))
    allowed_origins: List[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",
    ]

settings = Settings()
