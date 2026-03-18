from io import BytesIO
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field
from pypdf import PdfReader

from app.ai.groq_ai import answer_user_question, detect_fields_from_text, translate_pdf_text
from app.knowledge.document_checklists import DOCUMENT_CHECKLISTS
from app.ocr.ocr import detect_field_positions, extract_text_from_bytes, extract_text_from_file
from app.pdf.pdf_generator import (
    build_created_form_template,
    generate_created_form_pdf,
    generate_editor_pdf,
    generate_filled_pdf,
)
from app.templates.known_forms import build_known_form_pdf, get_known_form, list_known_forms
from app.translation.translator import translate_fields
from app.utils.file_handler import get_upload_path, save_upload_bytes


router = APIRouter()


def _get_upload_metadata(file_bytes: bytes, suffix: str) -> Dict[str, Any]:
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))
        page_sizes = [
            {
                "width": float(page.mediabox.width),
                "height": float(page.mediabox.height),
            }
            for page in reader.pages
        ]
        return {
            "source_type": "pdf",
            "page_count": len(page_sizes),
            "page_sizes": page_sizes,
        }

    with Image.open(BytesIO(file_bytes)) as image:
        width, height = image.size
    return {
        "source_type": "image",
        "page_count": 1,
        "page_sizes": [{"width": float(width), "height": float(height)}],
    }


class TranslateRequest(BaseModel):
    language: str = Field(..., examples=["Hindi"])
    fields: List[Dict[str, Any]]


class GeneratePdfRequest(BaseModel):
    upload_id: str
    original_filename: str
    language: str
    fields: List[Dict[str, Any]]
    form_data: Dict[str, str]
    signature: str
    extracted_text: str = ""
    signature_anchor: Dict[str, Any] | None = None


class ChatRequest(BaseModel):
    question: str
    history: List[Dict[str, str]] = []
    language: str = "English"


class PdfEditorUploadResponse(BaseModel):
    upload_id: str
    filename: str
    page_count: int
    page_sizes: List[Dict[str, float]]


class PdfEditorExportRequest(BaseModel):
    upload_id: str
    original_filename: str
    annotations: List[Dict[str, Any]]


class PdfEditorTranslateRequest(BaseModel):
    upload_id: str
    language: str = "English"


class CreateFormPdfRequest(BaseModel):
    form_title: str
    blocks: List[Dict[str, Any]]


class CustomTemplateStartRequest(BaseModel):
    form_title: str
    blocks: List[Dict[str, Any]]
    language: str = "English"


class KnownFormStartRequest(BaseModel):
    language: str = "English"


@router.post("/upload-form")
async def upload_form(file: UploadFile = File(...)) -> Dict:
    allowed_types = {".pdf", ".jpg", ".jpeg", ".png"}
    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()

    if suffix not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read uploaded file: {exc}") from exc

    try:
        upload_id, _saved_path = save_upload_bytes(file.filename or "form", file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to store uploaded file: {exc}") from exc

    try:
        upload_metadata = _get_upload_metadata(file_bytes, suffix)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to inspect uploaded file: {exc}") from exc

    try:
        extracted_text = extract_text_from_bytes(file_bytes, suffix)
    except Exception:
        extracted_text = ""

    try:
        detected_fields = detect_fields_from_text(extracted_text)
    except Exception:
        detected_fields = [
            {"label": "Name", "original_label": "Name", "type": "text"},
            {"label": "Date of Birth", "original_label": "Date of Birth", "type": "date"},
            {"label": "Address", "original_label": "Address", "type": "textarea"},
            {"label": "Phone", "original_label": "Phone", "type": "number"},
        ]

    positioned_fields, signature_anchor = detect_field_positions(file_bytes, suffix, detected_fields)
    translated_fields = translate_fields(positioned_fields, "English")

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "saved_path": "",
        "extracted_text": extracted_text,
        "detected_fields": translated_fields,
        "signature_anchor": signature_anchor,
        "source_type": upload_metadata["source_type"],
        "page_count": upload_metadata["page_count"],
        "page_sizes": upload_metadata["page_sizes"],
    }


@router.post("/editor/upload-pdf", response_model=PdfEditorUploadResponse)
async def upload_pdf_for_editor(file: UploadFile = File(...)) -> Dict[str, str]:
    filename = file.filename or "document.pdf"
    suffix = ""
    if "." in filename:
        suffix = "." + filename.rsplit(".", 1)[-1].lower()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, JPEG, and PNG files are supported in the form editor.")

    try:
        file_bytes = await file.read()
        upload_id, _saved_path = save_upload_bytes(filename, file_bytes)
        metadata = _get_upload_metadata(file_bytes, suffix)
        page_sizes = metadata["page_sizes"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to prepare the form editor file: {exc}") from exc

    return {
        "upload_id": upload_id,
        "filename": filename,
        "page_count": len(page_sizes),
        "page_sizes": page_sizes,
    }


@router.get("/upload-source/{upload_id}")
async def get_upload_source(upload_id: str) -> FileResponse:
    try:
        file_path = get_upload_path(upload_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Uploaded source file not found.") from exc

    suffix = file_path.suffix.lower()
    media_type = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix)
    return FileResponse(path=file_path, media_type=media_type)


@router.get("/upload-meta/{upload_id}")
async def get_upload_meta(upload_id: str) -> Dict[str, Any]:
    try:
        file_path = get_upload_path(upload_id)
        file_bytes = file_path.read_bytes()
        metadata = _get_upload_metadata(file_bytes, file_path.suffix.lower())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Uploaded source file not found.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to inspect uploaded file: {exc}") from exc

    return metadata


@router.post("/translate-fields")
async def translate_detected_fields(payload: TranslateRequest) -> Dict:
    translated_fields = translate_fields(payload.fields, payload.language)
    return {"language": payload.language, "fields": translated_fields}


@router.post("/generate-pdf")
async def generate_pdf(payload: GeneratePdfRequest) -> Dict:
    try:
        pdf_path = generate_filled_pdf(
            upload_id=payload.upload_id,
            original_filename=payload.original_filename,
            language=payload.language,
            fields=payload.fields,
            form_data=payload.form_data,
            signature_data_url=payload.signature,
            extracted_text=payload.extracted_text,
            signature_anchor=payload.signature_anchor,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    return {"pdf_url": f"/generated_pdfs/{pdf_path.name}", "language": payload.language}


@router.post("/editor/export-pdf")
async def export_edited_pdf(payload: PdfEditorExportRequest) -> Dict[str, str]:
    try:
        pdf_path = generate_editor_pdf(
            upload_id=payload.upload_id,
            original_filename=payload.original_filename,
            annotations=payload.annotations,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Form editor export failed: {exc}") from exc

    return {"pdf_url": f"/generated_pdfs/{pdf_path.name}"}


@router.post("/editor/translate-pdf")
async def translate_pdf_for_reading(payload: PdfEditorTranslateRequest) -> Dict[str, str]:
    try:
        file_path = get_upload_path(payload.upload_id)
        extracted_text = extract_text_from_file(file_path)
        translation = translate_pdf_text(extracted_text, payload.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF translation failed: {exc}") from exc

    return {
        "language": payload.language,
        "extracted_text": extracted_text,
        "translated_text": translation["translated_text"],
        "source": translation["source"],
        "error": translation["error"],
    }


@router.post("/create-form-pdf")
async def create_form_pdf(payload: CreateFormPdfRequest) -> Dict[str, str]:
    try:
        pdf_path = generate_created_form_pdf(payload.form_title, payload.blocks)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Create form export failed: {exc}") from exc

    return {"pdf_url": f"/generated_pdfs/{pdf_path.name}"}


@router.get("/known-forms")
async def get_known_forms() -> Dict[str, Any]:
    return {"items": list_known_forms()}


@router.post("/known-forms/{template_id}/start")
async def start_known_form(template_id: str, payload: KnownFormStartRequest) -> Dict[str, Any]:
    try:
        template = get_known_form(template_id)
        pdf_bytes = build_known_form_pdf(template)
        upload_id, _saved_path = save_upload_bytes(template["filename"], pdf_bytes)
        upload_metadata = _get_upload_metadata(pdf_bytes, ".pdf")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Known form template not found.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to start known form: {exc}") from exc

    translated_fields = translate_fields(template["fields"], payload.language)
    return {
        "upload_id": upload_id,
        "filename": template["filename"],
        "saved_path": "",
        "extracted_text": "",
        "detected_fields": translated_fields,
        "signature_anchor": template.get("signature_anchor"),
        "template_id": template["id"],
        "template_name": template["name"],
        "source_type": upload_metadata["source_type"],
        "page_count": upload_metadata["page_count"],
        "page_sizes": upload_metadata["page_sizes"],
    }


@router.post("/known-forms/custom/start")
async def start_custom_template(payload: CustomTemplateStartRequest) -> Dict[str, Any]:
    try:
        template = build_created_form_template(payload.form_title, payload.blocks)
        upload_id, _saved_path = save_upload_bytes(template["filename"], template["pdf_bytes"])
        upload_metadata = _get_upload_metadata(template["pdf_bytes"], ".pdf")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to start custom template: {exc}") from exc

    translated_fields = translate_fields(template["fields"], payload.language)
    return {
        "upload_id": upload_id,
        "filename": template["filename"],
        "saved_path": "",
        "extracted_text": "",
        "detected_fields": translated_fields,
        "signature_anchor": template.get("signature_anchor"),
        "template_id": "custom",
        "template_name": payload.form_title,
        "source_type": upload_metadata["source_type"],
        "page_count": upload_metadata["page_count"],
        "page_sizes": upload_metadata["page_sizes"],
    }


@router.get("/document-checklists")
async def get_document_checklists() -> Dict[str, Any]:
    return {"items": DOCUMENT_CHECKLISTS}


@router.post("/chat")
async def chat_with_formsathi(payload: ChatRequest) -> Dict[str, str]:
    return answer_user_question(payload.question, payload.history, payload.language)
