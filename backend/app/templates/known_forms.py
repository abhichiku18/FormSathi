from io import BytesIO
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _field(label: str, field_type: str, x: float, y: float, width: float, height: float = 12) -> Dict[str, Any]:
    return {
        "label": label,
        "original_label": label,
        "type": field_type,
        "position": {
            "page": 0,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "multiline": field_type == "textarea",
        },
    }


KNOWN_FORMS: List[Dict[str, Any]] = [
    {
        "id": "driving_licence_form",
        "name": "Driving Licence Form",
        "purpose": "Apply for a learner or driving licence.",
        "description": "Template-based form with exact placement for common applicant details.",
        "filename": "driving_licence_form.pdf",
        "header": "Driving Licence Application Form",
        "department": "Transport Department",
        "instructions": [
            "Fill all details clearly in block letters.",
            "Attach identity and address proof before submission.",
            "Sign only in the applicant signature area.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Date of Birth", "date", 185, 609, 120),
            _field("Aadhaar", "number", 395, 609, 120),
            _field("Mobile Number", "number", 185, 569, 120),
            _field("State/Province", "text", 395, 569, 120),
            _field("Street Address", "textarea", 185, 509, 330, 34),
            _field("Zip/Postal Code", "number", 185, 449, 100),
            _field("Licence Type", "text", 395, 449, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "income_certificate_form",
        "name": "Income Certificate Form",
        "purpose": "Apply for an official family income certificate.",
        "description": "Pre-mapped form for income certificate requests.",
        "filename": "income_certificate_form.pdf",
        "header": "Income Certificate Application Form",
        "department": "Revenue Department",
        "instructions": [
            "Provide accurate family income details.",
            "Attach income proof and address proof documents.",
            "Use the signature area after verifying all details.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Father Name", "text", 185, 609, 300),
            _field("Street Address", "textarea", 185, 549, 330, 34),
            _field("Occupation", "text", 185, 489, 180),
            _field("Mobile Number", "number", 395, 489, 120),
            _field("Aadhaar", "number", 185, 449, 180),
            _field("Annual Income", "number", 395, 449, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "scholarship_form",
        "name": "Scholarship Form",
        "purpose": "Apply for student scholarship support.",
        "description": "Exact-placement scholarship application template for students.",
        "filename": "scholarship_form.pdf",
        "header": "Scholarship Application Form",
        "department": "Education Department",
        "instructions": [
            "Enter student details exactly as per school records.",
            "Attach mark sheets, bank details, and income proof.",
            "School verification is required before submission.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Class", "text", 185, 609, 120),
            _field("Roll Number", "text", 395, 609, 120),
            _field("School", "text", 185, 569, 330),
            _field("ERP ID", "text", 185, 529, 160),
            _field("Aadhaar", "number", 395, 529, 120),
            _field("Street Address", "textarea", 185, 469, 330, 34),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "school_admission_form",
        "name": "School Admission Form",
        "purpose": "Collect student details for new school admission.",
        "description": "School admission template with pre-placed student fields.",
        "filename": "school_admission_form.pdf",
        "header": "School Admission Form",
        "department": "School Administration",
        "instructions": [
            "Use the student's official documents while filling this form.",
            "Attach birth certificate, Aadhaar, and previous school records.",
            "Parent or guardian signature is mandatory.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Date of Birth", "date", 185, 609, 120),
            _field("Class", "text", 395, 609, 120),
            _field("School", "text", 185, 569, 330),
            _field("Mother Name", "text", 185, 529, 300),
            _field("Street Address", "textarea", 185, 469, 330, 34),
            _field("Mobile Number", "number", 185, 409, 150),
            _field("Zip/Postal Code", "number", 395, 409, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "bank_account_opening_form",
        "name": "Bank Account Opening Form",
        "purpose": "Open a new savings or current bank account.",
        "description": "Pre-mapped template for common bank account opening details.",
        "filename": "bank_account_opening_form.pdf",
        "header": "Bank Account Opening Form",
        "department": "Banking Services",
        "instructions": [
            "Fill details exactly as per your identity proof.",
            "Keep PAN, Aadhaar, and address proof ready.",
            "Sign in the applicant signature area only.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Date of Birth", "date", 185, 609, 120),
            _field("Aadhaar", "number", 395, 609, 120),
            _field("Mobile Number", "number", 185, 569, 150),
            _field("Street Address", "textarea", 185, 509, 330, 34),
            _field("State/Province", "text", 185, 449, 150),
            _field("Zip/Postal Code", "number", 395, 449, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "job_application_form",
        "name": "Job Application Form",
        "purpose": "Submit personal details for a job application.",
        "description": "Template-based job application with exact placement for common applicant details.",
        "filename": "job_application_form.pdf",
        "header": "Job Application Form",
        "department": "Recruitment Office",
        "instructions": [
            "Use the same name as on your official documents.",
            "Attach resume and identity documents if required.",
            "Verify contact information before signing.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Email Address", "email", 185, 609, 220),
            _field("Mobile Number", "number", 395, 609, 120),
            _field("Street Address", "textarea", 185, 549, 330, 34),
            _field("Occupation", "text", 185, 489, 180),
            _field("State/Province", "text", 395, 489, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
    {
        "id": "residence_certificate_form",
        "name": "Residence Certificate Form",
        "purpose": "Apply for a residence or domicile certificate.",
        "description": "Template-based certificate request with exact saved field positions.",
        "filename": "residence_certificate_form.pdf",
        "header": "Residence Certificate Application Form",
        "department": "Citizen Services Department",
        "instructions": [
            "Fill your present residential details carefully.",
            "Attach Aadhaar, address proof, and supporting records.",
            "Check that your name matches your official IDs.",
        ],
        "fields": [
            _field("Full Name", "text", 185, 649, 300),
            _field("Father Name", "text", 185, 609, 300),
            _field("Street Address", "textarea", 185, 549, 330, 34),
            _field("State/Province", "text", 185, 489, 150),
            _field("Country", "text", 395, 489, 120),
            _field("Zip/Postal Code", "number", 185, 449, 120),
            _field("Aadhaar", "number", 395, 449, 120),
        ],
        "signature_anchor": {"page": 0, "x": 360, "y": 165, "width": 150, "height": 36},
    },
]


def list_known_forms() -> List[Dict[str, str]]:
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "purpose": item["purpose"],
            "description": item["description"],
        }
        for item in KNOWN_FORMS
    ]


def get_known_form(template_id: str) -> Dict[str, Any]:
    for item in KNOWN_FORMS:
        if item["id"] == template_id:
            return item
    raise KeyError(template_id)


def build_known_form_pdf(template: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    pdf.setFillColor(colors.HexColor("#15367d"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(page_width / 2, page_height - 62, template["header"])

    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(colors.HexColor("#334155"))
    pdf.drawCentredString(page_width / 2, page_height - 82, template["department"])

    pdf.setStrokeColor(colors.HexColor("#94a3b8"))
    pdf.line(52, page_height - 94, page_width - 52, page_height - 94)

    instructions_y = page_height - 122
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(54, instructions_y, "Important Instructions")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#475569"))
    current_y = instructions_y - 18
    for item in template["instructions"]:
        pdf.drawString(62, current_y, f"- {item}")
        current_y -= 13

    for field in template["fields"]:
        position = field["position"]
        label_y = position["y"] + 4
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(54, label_y, f"{field['label']}:")
        pdf.setStrokeColor(colors.HexColor("#64748b"))
        if field["type"] == "textarea":
            pdf.line(position["x"], position["y"], position["x"] + position["width"], position["y"])
            pdf.line(position["x"], position["y"] - 16, position["x"] + position["width"], position["y"] - 16)
        else:
            pdf.line(position["x"], position["y"], position["x"] + position["width"], position["y"])

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(54, 176, "Declaration:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.drawString(54, 160, "I hereby declare that the information provided above is true to the best of my knowledge.")

    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(54, 126, "Date:")
    pdf.line(92, 124, 180, 124)
    pdf.drawString(320, 126, "Signature:")
    pdf.line(386, 124, 520, 124)

    pdf.save()
    return buffer.getvalue()
