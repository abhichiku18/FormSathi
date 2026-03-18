from typing import Dict, List


STOPWORDS = {
    "the",
    "for",
    "and",
    "how",
    "what",
    "kya",
    "ka",
    "ki",
    "ke",
    "to",
    "apply",
    "documents",
    "document",
    "required",
}


DOCUMENT_CHECKLISTS: List[Dict[str, object]] = [
    {
        "name": "PM Kisan Samman Nidhi",
        "purpose": "Financial support for farmers.",
        "benefit": "Rs 6000 per year in 3 installments.",
        "official_url": "https://pmkisan.gov.in/",
        "eligibility": [
            "Small and marginal farmers",
            "Must own agricultural land",
        ],
        "documents": [
            "Aadhaar Card",
            "Land Ownership Documents",
            "Bank Account Details",
            "Mobile Number",
            "Passport Size Photo",
        ],
    },
    {
        "name": "Ayushman Bharat (PMJAY)",
        "purpose": "Health insurance for poor families.",
        "benefit": "Rs 5 lakh free medical treatment per year.",
        "official_url": "https://pmjay.gov.in/",
        "eligibility": [
            "Low-income families",
            "Listed in SECC database",
        ],
        "documents": [
            "Aadhaar Card",
            "Ration Card",
            "Family ID",
            "Mobile Number",
            "Residence Proof",
        ],
    },
    {
        "name": "PM Awas Yojana",
        "purpose": "Affordable housing for poor families.",
        "benefit": "Subsidy for building or buying a house.",
        "official_url": "https://pmaymis.gov.in/",
        "eligibility": [
            "Economically weaker section (EWS)",
            "No permanent house",
        ],
        "documents": [
            "Aadhaar Card",
            "Income Certificate",
            "Bank Passbook",
            "Residence Proof",
            "Passport Photo",
        ],
    },
    {
        "name": "Sukanya Samriddhi Yojana",
        "purpose": "Savings scheme for girl child.",
        "benefit": "High interest savings account.",
        "official_url": "https://www.indiapost.gov.in/Financial/Pages/Content/Post-Office-Saving-Schemes.aspx",
        "eligibility": [
            "Girl child below 10 years",
        ],
        "documents": [
            "Birth Certificate of Girl Child",
            "Aadhaar Card of Parent",
            "Address Proof",
            "Passport Photo",
            "Bank Account Details",
        ],
    },
    {
        "name": "Pradhan Mantri Mudra Yojana",
        "purpose": "Loan for small businesses.",
        "benefit": "Loan up to Rs 10 lakh.",
        "official_url": "https://www.mudra.org.in/",
        "eligibility": [
            "Small entrepreneurs",
            "Shop owners",
            "Startups",
        ],
        "documents": [
            "Aadhaar Card",
            "PAN Card",
            "Business Proof",
            "Bank Account Details",
            "Address Proof",
        ],
    },
    {
        "name": "National Scholarship Scheme",
        "purpose": "Financial support for students.",
        "benefit": "Scholarship for school and college students.",
        "official_url": "https://scholarships.gov.in/",
        "eligibility": [
            "Students from low-income families",
        ],
        "documents": [
            "Aadhaar Card",
            "Income Certificate",
            "School or College ID",
            "Bank Account Details",
            "Passport Photo",
        ],
    },
    {
        "name": "PM Ujjwala Yojana",
        "purpose": "Free LPG connection for poor households.",
        "benefit": "Free LPG connection.",
        "official_url": "https://www.pmuy.gov.in/",
        "eligibility": [
            "Women from BPL families",
        ],
        "documents": [
            "Aadhaar Card",
            "BPL Ration Card",
            "Address Proof",
            "Passport Photo",
            "Bank Account Details",
        ],
    },
    {
        "name": "Atal Pension Yojana",
        "purpose": "Pension scheme for unorganized workers.",
        "benefit": "Rs 1000 to Rs 5000 monthly pension after 60 years.",
        "official_url": "https://www.npscra.nsdl.co.in/scheme-details.php",
        "eligibility": [
            "Age between 18 and 40 years",
        ],
        "documents": [
            "Aadhaar Card",
            "Bank Account Details",
            "Mobile Number",
            "Address Proof",
            "Passport Photo",
        ],
    },
    {
        "name": "Startup India Scheme",
        "purpose": "Support for startups.",
        "benefit": "Tax benefits and funding support.",
        "official_url": "https://www.startupindia.gov.in/",
        "eligibility": [
            "Recognized startups",
            "Innovative business ideas",
        ],
        "documents": [
            "PAN Card",
            "Company Registration Certificate",
            "Business Plan",
            "Bank Account Details",
            "Identity Proof",
        ],
    },
    {
        "name": "PM Suraksha Bima Yojana",
        "purpose": "Accident insurance scheme.",
        "benefit": "Rs 2 lakh accident insurance.",
        "official_url": "https://jansuraksha.gov.in/",
        "eligibility": [
            "Age 18 to 70 years",
        ],
        "documents": [
            "Aadhaar Card",
            "Bank Account Details",
            "Mobile Number",
            "Address Proof",
            "Passport Photo",
        ],
    },
    {
        "name": "PAN Card",
        "purpose": "Permanent Account Number for tax and identity use.",
        "benefit": "Required for income tax, banking, and financial transactions.",
        "official_url": "https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html",
        "eligibility": [
            "Indian citizens",
            "Businesses and entities requiring PAN registration",
        ],
        "documents": [
            "Aadhaar Card",
            "Passport Photo",
            "Address Proof",
            "Identity Proof",
        ],
    },
    {
        "name": "Income Certificate",
        "purpose": "Proof of annual family income for government services and schemes.",
        "benefit": "Needed for scholarships, reservations, and welfare benefits.",
        "official_url": "https://services.india.gov.in/",
        "eligibility": [
            "Residents applying for official income verification",
        ],
        "documents": [
            "Aadhaar Card",
            "Address Proof",
            "Income Proof or Salary Slip",
            "Ration Card or Family ID",
            "Passport Photo",
        ],
    },
]


def format_checklists_for_prompt() -> str:
    sections: List[str] = []
    for item in DOCUMENT_CHECKLISTS:
        sections.append(
            "\n".join(
                [
                    f"Name: {item['name']}",
                    f"Purpose: {item['purpose']}",
                    f"Benefit: {item['benefit']}",
                    "Eligibility: " + ", ".join(item["eligibility"]),
                    "Documents: " + ", ".join(item["documents"]),
                ]
            )
        )
    return "\n\n".join(sections)


def search_checklists(query: str) -> List[Dict[str, object]]:
    normalized_query = query.lower()
    tokens = [token for token in normalized_query.replace("?", " ").split() if len(token) > 2 and token not in STOPWORDS]
    matches: List[Dict[str, object]] = []
    for item in DOCUMENT_CHECKLISTS:
        haystack = " ".join(
            [
                item["name"],
                item["purpose"],
                item["benefit"],
                " ".join(item["eligibility"]),
                " ".join(item["documents"]),
            ]
        ).lower()
        score = 0
        if item["name"].lower() in normalized_query or normalized_query in item["name"].lower():
            score += 100
        score += sum(10 for token in tokens if token in item["name"].lower())
        score += sum(3 for token in tokens if token in haystack)
        if score > 0:
            matches.append((score, item))
    matches.sort(key=lambda entry: entry[0], reverse=True)
    return [item for _, item in matches[:3]]
