from io import BytesIO
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from PIL import Image
from pypdf import PdfReader
import pytesseract
from pytesseract import Output

from app.config import settings


if settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


DEFAULT_OCR_TEXT = (
    "Application Form\n"
    "Name:\n"
    "Date of Birth:\n"
    "Address:\n"
    "Phone:\n"
    "Email:\n"
)

TEXTAREA_TYPES = {"textarea"}
LABEL_VARIANTS = {
    "name": ["full name", "name"],
    "mobile": ["mobile number", "mobile", "phone number", "phone"],
    "phone": ["phone number", "phone", "mobile number", "mobile"],
    "email": ["email address", "email"],
    "address": ["street address", "residential address", "address"],
    "street address": ["street address", "address"],
    "city": ["city"],
    "state province": ["state/province", "state province", "state"],
    "zip postal code": ["zip/postal code", "zip postal code", "zip"],
    "date": ["date"],
    "date of birth": ["date of birth", "dob"],
    "signature": ["signature"],
}


def _extract_text_from_pdf(file_path: Path) -> str:
    text_chunks: List[str] = []
    try:
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text)
    except Exception:
        return ""
    return "\n".join(text_chunks).strip()


def _extract_text_from_image(file_path: Path) -> str:
    try:
        with Image.open(file_path) as image:
            return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


def _extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text_chunks: List[str] = []
    try:
        reader = PdfReader(BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text)
    except Exception:
        return ""
    return "\n".join(text_chunks).strip()


def _extract_text_from_image_bytes(file_bytes: bytes) -> str:
    try:
        with Image.open(BytesIO(file_bytes)) as image:
            return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


def extract_text_from_file(file_path: Path) -> str:
    try:
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            text = _extract_text_from_pdf(file_path)
        else:
            text = _extract_text_from_image(file_path)

        if text:
            return text
    except Exception:
        pass

    return DEFAULT_OCR_TEXT


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _estimate_text_width(text: str, font_size: float) -> float:
    return max(len(text.strip()) * max(font_size, 8) * 0.48, 8)


def _group_pdf_fragments(
    fragments: List[Dict[str, float]],
    page_index: int,
    page_width: float,
    page_height: float,
) -> List[Dict[str, float]]:
    grouped: Dict[int, List[Dict[str, float]]] = {}
    for fragment in fragments:
        bucket = int(round(fragment["y"] / 6.0) * 6)
        grouped.setdefault(bucket, []).append(fragment)

    lines: List[Dict[str, float]] = []
    for bucket, parts in grouped.items():
        ordered = sorted(parts, key=lambda item: item["x"])
        line_text = " ".join(part["text"] for part in ordered if part["text"]).strip()
        if not line_text:
            continue

        min_x = min(part["x"] for part in ordered)
        max_x = max(part["x"] + part["width"] for part in ordered)
        line_height = max(part["height"] for part in ordered)
        baseline_y = max(page_height - float(bucket) - line_height, 24)
        lines.append(
            {
                "page": page_index,
                "text": line_text,
                "normalized": _normalize_text(line_text),
                "parts": ordered,
                "x": min_x,
                "y": baseline_y,
                "width": max_x - min_x,
                "height": line_height,
                "page_width": page_width,
                "page_height": page_height,
            }
        )

    return sorted(lines, key=lambda item: (-item["page"], -item["y"], item["x"]))


def _extract_pdf_line_items(file_bytes: bytes) -> List[Dict[str, float]]:
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception:
        return []

    lines: List[Dict[str, float]] = []
    for page_index, page in enumerate(reader.pages):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        fragments: List[Dict[str, float]] = []
        last_y = 0.0

        def visitor_text(text: str, cm, tm, _font_dict, font_size: float) -> None:
            nonlocal last_y
            cleaned = " ".join((text or "").split())
            if not cleaned:
                return

            tm_x = float(tm[4]) if len(tm) > 4 else 0.0
            tm_y = float(tm[5]) if len(tm) > 5 else 0.0
            cm_x = float(cm[4]) if len(cm) > 4 else 0.0
            cm_y = float(cm[5]) if len(cm) > 5 else 0.0
            x = tm_x if tm_x > 0 else cm_x
            if tm_y > 0:
                y = tm_y
                last_y = tm_y
            elif last_y > 0:
                y = last_y
            else:
                y = cm_y
            fragments.append(
                {
                    "text": cleaned,
                    "x": x,
                    "y": y,
                    "width": _estimate_text_width(cleaned, font_size or 10),
                    "height": max(font_size or 10, 10),
                }
            )

        try:
            page.extract_text(visitor_text=visitor_text)
        except Exception:
            continue

        lines.extend(_group_pdf_fragments(fragments, page_index, page_width, page_height))

    return lines


def _extract_image_line_items(file_bytes: bytes) -> List[Dict[str, float]]:
    try:
        with Image.open(BytesIO(file_bytes)) as image:
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            data = pytesseract.image_to_data(rgb_image, output_type=Output.DICT)
    except Exception:
        return []

    grouped: Dict[Tuple[int, int, int], List[Dict[str, float]]] = {}
    count = len(data.get("text", []))
    for index in range(count):
        text = (data["text"][index] or "").strip()
        if not text:
            continue

        key = (
            int(data.get("block_num", [0] * count)[index]),
            int(data.get("par_num", [0] * count)[index]),
            int(data.get("line_num", [0] * count)[index]),
        )
        grouped.setdefault(key, []).append(
            {
                "text": text,
                "x": float(data["left"][index]),
                "y_top": float(data["top"][index]),
                "width": float(data["width"][index]),
                "height": float(data["height"][index]),
            }
        )

    lines: List[Dict[str, float]] = []
    for words in grouped.values():
        ordered = sorted(words, key=lambda item: item["x"])
        line_text = " ".join(word["text"] for word in ordered).strip()
        if not line_text:
            continue

        min_x = min(word["x"] for word in ordered)
        min_y = min(word["y_top"] for word in ordered)
        max_x = max(word["x"] + word["width"] for word in ordered)
        max_y = max(word["y_top"] + word["height"] for word in ordered)
        line_height = max_y - min_y
        baseline_y = height - min_y - (line_height * 0.8)
        lines.append(
            {
                "page": 0,
                "text": line_text,
                "normalized": _normalize_text(line_text),
                "parts": ordered,
                "x": min_x,
                "y": baseline_y,
                "width": max_x - min_x,
                "height": line_height,
                "page_width": float(width),
                "page_height": float(height),
            }
        )

    return sorted(lines, key=lambda item: (-item["y"], item["x"]))


def _find_anchor(lines: List[Dict[str, float]], label: str) -> Optional[Dict[str, float]]:
    normalized_label = _normalize_text(label)
    if not normalized_label:
        return None

    variants = LABEL_VARIANTS.get(normalized_label, [normalized_label])
    label_tokens = set(normalized_label.split())
    best_match: Optional[Dict[str, float]] = None
    best_score = 0.0

    for line in lines:
        normalized_line = line.get("normalized", "")
        if not normalized_line:
            continue

        line_tokens = set(normalized_line.split())
        score = 0.0
        for variant in variants:
            if variant in normalized_line:
                score = max(score, 20 + len(variant))

        if score == 0:
            overlap = len(label_tokens & line_tokens)
            score = float(overlap)

        if score > best_score:
            best_score = score
            best_match = line

    return best_match if best_score > 0 else None


def _resolve_anchor_span(anchor: Dict[str, float], label: str) -> Tuple[float, Optional[float]]:
    parts = anchor.get("parts") or []
    if not parts:
        return float(anchor["x"] + anchor["width"]), None

    normalized_label = _normalize_text(label)
    variants = LABEL_VARIANTS.get(normalized_label, [normalized_label])
    label_tokens = set(normalized_label.split())
    best_index = -1
    best_end_x = float(anchor["x"] + anchor["width"])
    best_score = 0.0

    for index, part in enumerate(parts):
        part_text = part.get("text", "")
        normalized_part = _normalize_text(part_text)
        if not normalized_part:
            continue

        part_tokens = set(normalized_part.split())
        score = 0.0
        for variant in variants:
            if variant in normalized_part:
                score = max(score, 20 + len(variant))

        if score == 0:
            overlap = len(label_tokens & part_tokens)
            score = float(overlap)

        if score > best_score:
            best_score = score
            best_index = index
            best_end_x = float(part.get("x", anchor["x"]) + part.get("width", anchor["width"]))

    next_part_x = None
    if best_index >= 0 and best_index + 1 < len(parts):
        next_part_x = float(parts[best_index + 1].get("x", 0))

    return best_end_x, next_part_x


def _build_position(anchor: Dict[str, float], field_type: str, label: str) -> Dict[str, float]:
    end_x, next_part_x = _resolve_anchor_span(anchor, label)
    input_x = min(end_x + 18, anchor["page_width"] - 120)
    if next_part_x and next_part_x > input_x + 24:
        available_width = max(next_part_x - input_x - 18, 72)
    else:
        available_width = max(anchor["page_width"] - input_x - 42, 96)
    line_height = max(anchor["height"], 12)
    y_offset = 2 if field_type in TEXTAREA_TYPES else 1
    return {
        "page": int(anchor["page"]),
        "x": round(input_x, 2),
        "y": round(anchor["y"] - y_offset, 2),
        "width": round(available_width, 2),
        "height": round(line_height, 2),
        "multiline": field_type in TEXTAREA_TYPES,
    }


def detect_field_positions(
    file_bytes: bytes,
    suffix: str,
    fields: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], Optional[Dict[str, float]]]:
    lines = _extract_pdf_line_items(file_bytes) if suffix == ".pdf" else _extract_image_line_items(file_bytes)
    positioned_fields: List[Dict[str, str]] = []

    for field in fields:
        original_label = field.get("original_label") or field.get("label") or "Field"
        anchor = _find_anchor(lines, original_label)
        updated_field = dict(field)
        if anchor:
            updated_field["position"] = _build_position(anchor, field.get("type", "text"), original_label)
        positioned_fields.append(updated_field)

    signature_anchor = None
    anchor = _find_anchor(lines, "signature")
    if anchor:
        signature_anchor = _build_position(anchor, "textarea", "signature")

    return positioned_fields, signature_anchor


def extract_text_from_bytes(file_bytes: bytes, suffix: str) -> str:
    try:
        if suffix == ".pdf":
            text = _extract_text_from_pdf_bytes(file_bytes)
        else:
            text = _extract_text_from_image_bytes(file_bytes)

        if text:
            return text
    except Exception:
        pass

    return DEFAULT_OCR_TEXT
