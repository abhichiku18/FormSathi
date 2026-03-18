import json
import logging
import re
from typing import Dict, List, Optional

from groq import Groq

from app.config import settings
from app.knowledge.document_checklists import DOCUMENT_CHECKLISTS, format_checklists_for_prompt, search_checklists


logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """
You are an AI assistant that extracts fillable form fields from OCR text.
Return valid JSON only in this exact shape:
{"fields":[{"label":"Name","type":"text"}]}

Rules:
- Detect only fields a person would fill.
- Allowed types: text, date, number, email, textarea
- Use textarea for long addresses or descriptions.
- If unsure, use text.

OCR Text:
{ocr_text}
""".strip()

CHATBOT_PROMPT_TEMPLATE = """
You are the FormSathi assistant.
Answer any question asked by the user.
You can answer government and non-government questions.
You are especially useful for government schemes, certificates, ID documents, required documents, portals, eligibility, and application processes.
Use the knowledge base below only when relevant.
Do not behave as if you are limited to government topics.
Keep answers concise, practical, and easy to read.
Prefer 2 to 6 short sentences, or 3 to 5 short bullets when bullets help.
If the user asks for steps, give the main steps only.
If something varies by state, office, or portal, mention that briefly.
If you are unsure, say so briefly and give the best next step.

Knowledge Base:
{knowledge_base}

Recent conversation:
{history}

User question:
{question}
""".strip()

GENERAL_SYSTEM_PROMPT = (
    "You are a concise and helpful assistant. "
    "Answer clearly in 2 to 6 short sentences or 3 to 5 short bullets when useful."
)

SUPPORTED_CHAT_LANGUAGES = {"english", "hindi", "bengali", "tamil", "marathi"}

GOVERNMENT_KEYWORDS = [
    "scheme",
    "schemes",
    "certificate",
    "certificates",
    "aadhaar",
    "aadhar",
    "pan",
    "ration card",
    "income certificate",
    "caste certificate",
    "domicile",
    "residence certificate",
    "scholarship",
    "yojana",
    "application",
    "documents",
    "document",
    "eligibility",
    "portal",
    "license",
    "licence",
    "driving licence",
    "driving license",
]

CANONICAL_FIELD_MAP = {
    "name": ("Full Name", "text"),
    "full name": ("Full Name", "text"),
    "email": ("Email Address", "email"),
    "email address": ("Email Address", "email"),
    "mobile": ("Mobile Number", "number"),
    "mobile number": ("Mobile Number", "number"),
    "phone": ("Phone Number", "number"),
    "phone number": ("Phone Number", "number"),
    "address": ("Street Address", "textarea"),
    "street address": ("Street Address", "textarea"),
    "state": ("State/Province", "text"),
    "state province": ("State/Province", "text"),
    "zip": ("Zip/Postal Code", "number"),
    "zip postal code": ("Zip/Postal Code", "number"),
}


def _heuristic_detect_fields(text: str) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    seen = set()
    patterns = [
        ("Full Name", "text"),
        ("Date of Birth", "date"),
        ("DOB", "date"),
        ("Email", "email"),
        ("Email Address", "email"),
        ("Phone", "number"),
        ("Mobile", "number"),
        ("Mobile Number", "number"),
        ("Address", "textarea"),
        ("Street Address", "textarea"),
        ("City", "text"),
        ("State", "text"),
        ("State/Province", "text"),
        ("Zip", "number"),
        ("Zip/Postal Code", "number"),
        ("Name", "text"),
        ("Father Name", "text"),
        ("Mother Name", "text"),
        ("Occupation", "text"),
        ("Aadhaar", "number"),
        ("Date", "date"),
        ("Signature", "text"),
    ]

    for label, field_type in patterns:
        if re.search(rf"\b{re.escape(label)}\b", text, re.IGNORECASE) and label not in seen:
            candidates.append({"label": label, "type": field_type})
            seen.add(label)

    if not candidates:
        for raw_line in text.splitlines():
            matches = re.findall(r"([A-Za-z][A-Za-z/ ]{1,40}?):", raw_line)
            for match in matches:
                normalized = " ".join(match.split()).title()
                if normalized and normalized not in seen:
                    lowered = normalized.lower()
                    if "email" in lowered:
                        field_type = "email"
                    elif "date" in lowered or "dob" in lowered:
                        field_type = "date"
                    elif any(token in lowered for token in ["phone", "mobile", "zip", "postal", "aadhaar"]):
                        field_type = "number"
                    elif "address" in lowered:
                        field_type = "textarea"
                    else:
                        field_type = "text"
                    candidates.append({"label": normalized, "type": field_type})
                    seen.add(normalized)

    if not candidates:
        candidates = [
            {"label": "Name", "type": "text"},
            {"label": "Date of Birth", "type": "date"},
            {"label": "Address", "type": "textarea"},
            {"label": "Phone", "type": "number"},
        ]

    return candidates


def _normalize_fields(fields: List[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    seen = set()
    for field in fields:
        label = (field.get("label") or "Field").strip()
        field_type = (field.get("type") or "text").strip().lower()
        normalized_key = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
        if normalized_key in CANONICAL_FIELD_MAP:
            label, field_type = CANONICAL_FIELD_MAP[normalized_key]
        if field_type not in {"text", "date", "number", "email", "textarea"}:
            field_type = "text"
        if label in seen:
            continue
        seen.add(label)
        normalized.append(
            {
                "label": label,
                "original_label": label,
                "type": field_type,
            }
        )
    return normalized


def detect_fields_from_text(ocr_text: str) -> List[Dict[str, str]]:
    if settings.groq_api_key:
        try:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model=settings.groq_model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": PROMPT_TEMPLATE.format(ocr_text=ocr_text[:12000])},
                ],
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            fields = parsed.get("fields", [])
            if fields:
                return _normalize_fields(fields)
        except Exception:
            pass

    return _normalize_fields(_heuristic_detect_fields(ocr_text))


def _fallback_chat_response(question: str) -> str:
    lower_question = question.lower()
    exact_named_match = next(
        (item for item in DOCUMENT_CHECKLISTS if item["name"].lower() in lower_question),
        None,
    )

    if exact_named_match:
        return "\n".join(
            [
                exact_named_match["name"],
                f"Purpose: {exact_named_match['purpose']}",
                f"Benefit: {exact_named_match['benefit']}",
                "Eligibility: " + ", ".join(exact_named_match["eligibility"]),
                "Documents Required: " + ", ".join(exact_named_match["documents"]),
            ]
        )

    return "I could not get a live model answer right now. Please try again in a moment."


def _is_government_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in GOVERNMENT_KEYWORDS)


def _build_chat_messages(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    language: str = "English",
) -> List[Dict[str, str]]:
    normalized_language = (language or "English").strip().title()
    if normalized_language.lower() not in SUPPORTED_CHAT_LANGUAGES:
        normalized_language = "English"

    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"{GENERAL_SYSTEM_PROMPT} "
                f"Reply in {normalized_language}."
            ),
        }
    ]

    if _is_government_question(question):
        knowledge_base = format_checklists_for_prompt()
        messages.append(
            {
                "role": "system",
                "content": (
                    "You are especially helpful for Indian government services, schemes, certificates, "
                    "application processes, eligibility, and required documents. "
                    "Use this knowledge only when relevant:\n\n"
                    f"{knowledge_base}"
                ),
            }
        )

    for item in (history or [])[-6:]:
        role = item.get("role", "user")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant", "system"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})
    return messages


def answer_user_question(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    language: str = "English",
) -> Dict[str, str]:
    error_message = ""

    if settings.groq_api_key:
        try:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model=settings.groq_model,
                temperature=0.3,
                messages=_build_chat_messages(question, history, language),
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return {"answer": content, "source": "groq", "error": ""}
        except Exception as exc:
            error_message = str(exc)
            logger.exception("Groq chat request failed")

    return {"answer": _fallback_chat_response(question), "source": "fallback", "error": error_message}


def translate_pdf_text(text: str, language: str) -> Dict[str, str]:
    normalized_language = (language or "English").strip().title()
    if normalized_language.lower() not in SUPPORTED_CHAT_LANGUAGES:
        normalized_language = "English"

    trimmed_text = (text or "").strip()
    if not trimmed_text:
        return {"translated_text": "", "source": "fallback", "error": ""}

    if normalized_language == "English":
        return {"translated_text": trimmed_text, "source": "local", "error": ""}

    if settings.groq_api_key:
        try:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model=settings.groq_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Translate the following PDF text into {normalized_language}. "
                            "Keep headings and structure readable. "
                            "Do not add explanations."
                        ),
                    },
                    {"role": "user", "content": trimmed_text[:12000]},
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return {"translated_text": content, "source": "groq", "error": ""}
        except Exception as exc:
            logger.exception("Groq PDF translation request failed")
            return {"translated_text": trimmed_text, "source": "fallback", "error": str(exc)}

    return {"translated_text": trimmed_text, "source": "fallback", "error": ""}
