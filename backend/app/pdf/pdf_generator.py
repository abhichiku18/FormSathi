import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

from app.config import settings
from app.utils.file_handler import decode_signature_data_url, get_upload_path


def _safe_filename(name: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in name)


def _draw_value(
    pdf: canvas.Canvas,
    value: str,
    position: Dict[str, float],
    field_type: str,
) -> None:
    if not value:
        return

    width = float(position.get("width", 220))
    font_size = max(min(float(position.get("height", 12)), 12), 9)
    if width < 120:
        font_size = max(min(font_size, 10), 8.5)
    x = float(position.get("x", 36))
    y = float(position.get("y", 36))

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica", font_size)

    if position.get("multiline") or field_type == "textarea":
        text_object = pdf.beginText()
        text_object.setTextOrigin(x, y)
        text_object.setFont("Helvetica", font_size)
        lines = simpleSplit(str(value), "Helvetica", font_size, width)
        for line in lines[:3]:
            text_object.textLine(line)
        pdf.drawText(text_object)
        return

    text = str(value).strip()
    while font_size > 7.5 and pdf.stringWidth(text, "Helvetica", font_size) > width:
        font_size -= 0.5
    pdf.setFont("Helvetica", font_size)
    pdf.drawString(x, y, text)


def _draw_signature(
    pdf: canvas.Canvas,
    signature_bytes: bytes,
    anchor: Optional[Dict[str, float]],
    page_width: float,
    page_height: float,
) -> None:
    if not signature_bytes:
        return

    x = float(anchor.get("x", page_width - 180)) if anchor else page_width - 180
    y = float(anchor.get("y", 72)) if anchor else 72
    width = min(float(anchor.get("width", 150)) if anchor else 150, 180)
    height = max(float(anchor.get("height", 36)) if anchor else 36, 36) * 1.6

    signature_image = ImageReader(BytesIO(signature_bytes))
    pdf.drawImage(signature_image, x, y - 10, width=width, height=height, mask="auto")


def _fallback_summary_pdf(
    pdf_path: Path,
    original_filename: str,
    language: str,
    fields: List[Dict[str, str]],
    form_data: Dict[str, str],
    signature_data_url: str,
    extracted_text: str = "",
) -> Path:
    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=(595.27, 841.89))
    width, height = 595.27, 841.89

    pdf.setFillColor(colors.HexColor("#312e81"))
    pdf.roundRect(36, height - 100, width - 72, 52, 14, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(54, height - 78, "FormSathi - Completed Form")

    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(54, height - 116, f"Original file: {original_filename}")
    pdf.drawString(54, height - 132, f"Language: {language}")

    y_position = height - 172
    for field in fields:
        label = field.get("label", "Field")
        original_label = field.get("original_label", label)
        value = form_data.get(original_label, "")

        if y_position < 120:
            pdf.showPage()
            y_position = height - 60

        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(54, y_position, f"{label}:")

        pdf.setFillColor(colors.HexColor("#334155"))
        pdf.setFont("Helvetica", 11)
        lines = str(value or "Not provided").splitlines() or ["Not provided"]
        for line in lines:
            pdf.drawString(170, y_position, line[:80])
            y_position -= 16

        y_position -= 10

    if extracted_text:
        if y_position < 180:
            pdf.showPage()
            y_position = height - 60

        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(54, y_position, "OCR Extract Preview:")
        y_position -= 18

        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(colors.HexColor("#475569"))
        for line in extracted_text.splitlines()[:10]:
            pdf.drawString(54, y_position, line[:100])
            y_position -= 12

    signature_bytes = decode_signature_data_url(signature_data_url)
    if signature_bytes:
        _draw_signature(pdf, signature_bytes, None, width, height)

    pdf.save()
    pdf_path.write_bytes(packet.getvalue())
    return pdf_path


def _overlay_on_pdf(
    original_path: Path,
    pdf_path: Path,
    fields: List[Dict[str, str]],
    form_data: Dict[str, str],
    signature_bytes: bytes,
    signature_anchor: Optional[Dict[str, float]],
) -> Path:
    reader = PdfReader(str(original_path))
    writer = PdfWriter()

    signature_page = int(signature_anchor.get("page", 0)) if signature_anchor else 0

    for page_index, original_page in enumerate(reader.pages):
        page_width = float(original_page.mediabox.width)
        page_height = float(original_page.mediabox.height)
        overlay_stream = BytesIO()
        overlay_pdf = canvas.Canvas(overlay_stream, pagesize=(page_width, page_height))

        has_overlay = False
        for field in fields:
            position = field.get("position")
            original_label = field.get("original_label") or field.get("label") or "Field"
            value = str(form_data.get(original_label, "")).strip()
            if not position or int(position.get("page", 0)) != page_index or not value:
                continue
            _draw_value(overlay_pdf, value, position, field.get("type", "text"))
            has_overlay = True

        if signature_bytes and page_index == signature_page:
            _draw_signature(overlay_pdf, signature_bytes, signature_anchor, page_width, page_height)
            has_overlay = True

        overlay_pdf.save()

        if has_overlay:
            overlay_stream.seek(0)
            overlay_reader = PdfReader(overlay_stream)
            original_page.merge_page(overlay_reader.pages[0])

        writer.add_page(original_page)

    with pdf_path.open("wb") as output_file:
        writer.write(output_file)

    return pdf_path


def _overlay_on_image(
    original_path: Path,
    pdf_path: Path,
    fields: List[Dict[str, str]],
    form_data: Dict[str, str],
    signature_bytes: bytes,
    signature_anchor: Optional[Dict[str, float]],
) -> Path:
    image = ImageReader(str(original_path))
    image_width, image_height = image.getSize()
    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=(image_width, image_height))
    pdf.drawImage(image, 0, 0, width=image_width, height=image_height)

    for field in fields:
        position = field.get("position")
        original_label = field.get("original_label") or field.get("label") or "Field"
        value = str(form_data.get(original_label, "")).strip()
        if not position or int(position.get("page", 0)) != 0 or not value:
            continue
        _draw_value(pdf, value, position, field.get("type", "text"))

    _draw_signature(pdf, signature_bytes, signature_anchor, image_width, image_height)
    pdf.save()
    pdf_path.write_bytes(packet.getvalue())
    return pdf_path


def generate_filled_pdf(
    upload_id: str,
    original_filename: str,
    language: str,
    fields: List[Dict[str, str]],
    form_data: Dict[str, str],
    signature_data_url: str,
    extracted_text: str = "",
    signature_anchor: Optional[Dict[str, float]] = None,
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = _safe_filename(Path(original_filename).stem or "form")
    os.makedirs(settings.generated_pdfs_dir, exist_ok=True)
    pdf_path = Path(os.path.join(settings.generated_pdfs_dir, f"{base_name}_{timestamp}.pdf"))
    signature_bytes = decode_signature_data_url(signature_data_url)

    try:
        original_path = get_upload_path(upload_id)
    except FileNotFoundError:
        return _fallback_summary_pdf(
            pdf_path=pdf_path,
            original_filename=original_filename,
            language=language,
            fields=fields,
            form_data=form_data,
            signature_data_url=signature_data_url,
            extracted_text=extracted_text,
        )

    positioned_fields = [field for field in fields if field.get("position")]
    if not positioned_fields:
        return _fallback_summary_pdf(
            pdf_path=pdf_path,
            original_filename=original_filename,
            language=language,
            fields=fields,
            form_data=form_data,
            signature_data_url=signature_data_url,
            extracted_text=extracted_text,
        )

    if original_path.suffix.lower() == ".pdf":
        return _overlay_on_pdf(
            original_path=original_path,
            pdf_path=pdf_path,
            fields=fields,
            form_data=form_data,
            signature_bytes=signature_bytes,
            signature_anchor=signature_anchor,
        )

    if original_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        return _overlay_on_image(
            original_path=original_path,
            pdf_path=pdf_path,
            fields=fields,
            form_data=form_data,
            signature_bytes=signature_bytes,
            signature_anchor=signature_anchor,
        )

    return _fallback_summary_pdf(
        pdf_path=pdf_path,
        original_filename=original_filename,
        language=language,
        fields=fields,
        form_data=form_data,
        signature_data_url=signature_data_url,
        extracted_text=extracted_text,
    )


def _draw_editor_annotation(
    pdf: canvas.Canvas,
    annotation: Dict[str, object],
    page_width: float,
    page_height: float,
) -> None:
    annotation_type = str(annotation.get("type", ""))
    x = float(annotation.get("x_ratio", 0)) * page_width
    width = max(float(annotation.get("width_ratio", 0)) * page_width, 1)
    height = max(float(annotation.get("height_ratio", 0)) * page_height, 1)
    top_y = float(annotation.get("y_ratio", 0)) * page_height
    y = page_height - top_y - height

    if annotation_type == "highlight":
        pdf.setFillColor(colors.Color(1, 0.93, 0.35, alpha=0.5))
        pdf.rect(x, y, width, height, fill=1, stroke=0)
        return

    if annotation_type == "text":
        text = str(annotation.get("content", "")).strip()
        if not text:
            return
        font_size = max(min(float(annotation.get("font_size", 16)), 28), 8)
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica", font_size)
        raw_lines = text.splitlines() or [text]
        lines: List[str] = []
        available_width = max(width - 12, 12)
        for raw_line in raw_lines:
            wrapped = simpleSplit(raw_line or " ", "Helvetica", font_size, available_width)
            lines.extend(wrapped or [" "])
        baseline = y + max(height - font_size - 4, 0)
        if len(lines) > 1:
            text_object = pdf.beginText()
            text_object.setTextOrigin(x + 6, baseline)
            text_object.setFont("Helvetica", font_size)
            for line in lines[:5]:
                text_object.textLine(line)
            pdf.drawText(text_object)
        elif lines:
            pdf.drawString(x + 6, baseline, lines[0])
        return

    if annotation_type == "signature":
        signature_bytes = decode_signature_data_url(str(annotation.get("signature_data", "")))
        if signature_bytes:
            signature_image = ImageReader(BytesIO(signature_bytes))
            pdf.drawImage(signature_image, x, y, width=width, height=height, mask="auto")


def generate_editor_pdf(
    upload_id: str,
    original_filename: str,
    annotations: List[Dict[str, object]],
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = _safe_filename(Path(original_filename).stem or "edited_form")
    os.makedirs(settings.generated_pdfs_dir, exist_ok=True)
    pdf_path = Path(os.path.join(settings.generated_pdfs_dir, f"{base_name}_editor_{timestamp}.pdf"))

    original_path = get_upload_path(upload_id)
    suffix = original_path.suffix.lower()

    if suffix in {".jpg", ".jpeg", ".png"}:
        image = ImageReader(str(original_path))
        image_width, image_height = image.getSize()
        packet = BytesIO()
        pdf = canvas.Canvas(packet, pagesize=(image_width, image_height))
        pdf.drawImage(image, 0, 0, width=image_width, height=image_height)

        for annotation in annotations:
            _draw_editor_annotation(pdf, annotation, image_width, image_height)

        pdf.save()
        pdf_path.write_bytes(packet.getvalue())
        return pdf_path

    if suffix != ".pdf":
        raise ValueError("The form editor supports PDF, JPG, JPEG, and PNG files only.")

    reader = PdfReader(str(original_path))
    writer = PdfWriter()

    for page_index, original_page in enumerate(reader.pages):
        page_annotations = [item for item in annotations if int(item.get("page", 0)) == page_index]
        if not page_annotations:
            writer.add_page(original_page)
            continue

        page_width = float(original_page.mediabox.width)
        page_height = float(original_page.mediabox.height)
        overlay_stream = BytesIO()
        overlay_pdf = canvas.Canvas(overlay_stream, pagesize=(page_width, page_height))

        for annotation in page_annotations:
            _draw_editor_annotation(overlay_pdf, annotation, page_width, page_height)

        overlay_pdf.save()
        overlay_stream.seek(0)
        overlay_reader = PdfReader(overlay_stream)
        original_page.merge_page(overlay_reader.pages[0])
        writer.add_page(original_page)

    with pdf_path.open("wb") as output_file:
        writer.write(output_file)

    return pdf_path


def _draw_builder_block(pdf: canvas.Canvas, block: Dict[str, object], x: float, y: float, width: float) -> float:
    block_type = str(block.get("type", "field"))
    title = str(block.get("title", "")).strip()
    content = str(block.get("content", "")).strip()
    items = block.get("items") or []

    if block_type == "title":
        pdf.setFillColor(colors.HexColor("#15367d"))
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(x + (width / 2), y, content or title or "Form Title")
        return y - 28

    if block_type == "meta":
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, f"{title}:")
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor("#334155"))
        lines = simpleSplit(content or "__________________", "Helvetica", 11, width - 110)
        line_y = y
        for line in lines[:3]:
            pdf.drawString(x + 96, line_y, line)
            line_y -= 14
        return line_y - 4

    if block_type == "paragraph":
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, title or "Description")
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor("#334155"))
        line_y = y - 16
        for line in simpleSplit(content or "Add your content here.", "Helvetica", 11, width)[:8]:
            pdf.drawString(x, line_y, line)
            line_y -= 14
        return line_y - 2

    if block_type == "documents":
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, title or "Required Documents")
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor("#334155"))
        line_y = y - 18
        if not items:
            items = ["Document 1", "Document 2"]
        for item in items[:8]:
            pdf.drawString(x + 10, line_y, f"- {item}")
            line_y -= 14
        return line_y - 2

    if block_type == "signature":
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, title or "Signature")
        pdf.line(x + 110, y - 2, x + min(width, 320), y - 2)
        return y - 28

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, f"{title or 'Field'}:")
    pdf.setStrokeColor(colors.HexColor("#94a3b8"))
    pdf.line(x + 130, y - 2, x + min(width, 360), y - 2)
    return y - 26


def _builder_layout(blocks: List[Dict[str, object]]) -> Dict[str, object]:
    page_width, page_height = A4
    margin_x = 54
    content_width = page_width - (margin_x * 2)
    current_y = page_height - 64
    layout_pages: List[List[Dict[str, object]]] = [[]]
    page_index = 0
    generated_fields: List[Dict[str, object]] = []
    signature_anchor: Optional[Dict[str, float]] = None

    for block in blocks:
        if current_y < 90:
            layout_pages.append([])
            page_index += 1
            current_y = page_height - 64

        block_type = str(block.get("type", "field"))
        title = str(block.get("title", "")).strip() or "Field"
        content = str(block.get("content", "")).strip()
        items = list(block.get("items") or [])
        start_y = current_y

        if block_type == "title":
            next_y = current_y - 28
        elif block_type == "meta":
            lines = simpleSplit(content or "__________________", "Helvetica", 11, content_width - 110)
            next_y = current_y - (14 * max(len(lines), 1)) - 4
        elif block_type == "paragraph":
            lines = simpleSplit(content or "Add your content here.", "Helvetica", 11, content_width)
            next_y = current_y - 16 - (14 * min(len(lines), 8)) - 2
        elif block_type == "documents":
            next_y = current_y - 18 - (14 * max(min(len(items), 8), 2)) - 2
        elif block_type == "signature":
            next_y = current_y - 28
            signature_anchor = {"page": page_index, "x": margin_x + 240, "y": current_y - 2, "width": 150, "height": 36}
        else:
            next_y = current_y - 26
            generated_fields.append(
                {
                    "label": title,
                    "original_label": title,
                    "type": "textarea" if "address" in title.lower() else "text",
                    "position": {
                        "page": page_index,
                        "x": margin_x + 150,
                        "y": current_y - 2,
                        "width": min(content_width - 150, 240),
                        "height": 12,
                        "multiline": "address" in title.lower(),
                    },
                }
            )

        layout_pages[page_index].append(
            {
                "type": block_type,
                "title": title,
                "content": content,
                "items": items,
                "x": margin_x,
                "y": start_y,
                "width": content_width,
            }
        )
        current_y = next_y

    return {"pages": layout_pages, "fields": generated_fields, "signature_anchor": signature_anchor}


def generate_created_form_pdf(form_title: str, blocks: List[Dict[str, object]]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = _safe_filename(form_title or "created_form")
    os.makedirs(settings.generated_pdfs_dir, exist_ok=True)
    pdf_path = Path(os.path.join(settings.generated_pdfs_dir, f"{base_name}_builder_{timestamp}.pdf"))

    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=A4)
    layout = _builder_layout(blocks)

    for page_number, page_blocks in enumerate(layout["pages"]):
        if page_number > 0:
            pdf.showPage()
        for block in page_blocks:
            _draw_builder_block(pdf, block, block["x"], block["y"], block["width"])

    pdf.save()
    pdf_path.write_bytes(packet.getvalue())
    return pdf_path


def build_created_form_template(form_title: str, blocks: List[Dict[str, object]]) -> Dict[str, object]:
    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=A4)
    layout = _builder_layout(blocks)

    for page_number, page_blocks in enumerate(layout["pages"]):
        if page_number > 0:
            pdf.showPage()
        for block in page_blocks:
            _draw_builder_block(pdf, block, block["x"], block["y"], block["width"])

    pdf.save()
    return {
        "filename": f"{_safe_filename(form_title or 'custom_template')}.pdf",
        "pdf_bytes": packet.getvalue(),
        "fields": layout["fields"],
        "signature_anchor": layout["signature_anchor"],
    }
