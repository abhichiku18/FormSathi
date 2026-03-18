import base64
import os
from pathlib import Path
from uuid import uuid4

from app.config import settings


def save_upload_bytes(filename: str, file_bytes: bytes) -> tuple[str, Path]:
    extension = Path(filename or "").suffix.lower()
    upload_id = uuid4().hex
    os.makedirs(settings.upload_dir, exist_ok=True)
    destination_str = os.path.join(settings.upload_dir, f"{upload_id}{extension}")

    with open(destination_str, "wb") as output_file:
        output_file.write(file_bytes)

    return upload_id, Path(destination_str)


def get_upload_path(upload_id: str) -> Path:
    upload_dir = Path(settings.upload_dir)
    matches = list(upload_dir.glob(f"{upload_id}.*"))
    if not matches:
        raise FileNotFoundError(f"No uploaded file found for upload_id={upload_id}")
    return matches[0]


def decode_signature_data_url(signature_data_url: str) -> bytes:
    if not signature_data_url or "," not in signature_data_url:
        return b""

    _, encoded = signature_data_url.split(",", 1)
    return base64.b64decode(encoded)
