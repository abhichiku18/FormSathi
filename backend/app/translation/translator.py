from typing import Dict, List


TRANSLATIONS = {
    "Hindi": {
        "Full Name": "\u092a\u0942\u0930\u093e \u0928\u093e\u092e",
        "Name": "\u0928\u093e\u092e",
        "Date of Birth": "\u091c\u0928\u094d\u092e \u0924\u093f\u0925\u093f",
        "Date": "\u0924\u093f\u0925\u093f",
        "Street Address": "\u0938\u094d\u091f\u094d\u0930\u0940\u091f \u092a\u0924\u093e",
        "Address": "\u092a\u0924\u093e",
        "City": "\u0936\u0939\u0930",
        "State/Province": "\u0930\u093e\u091c\u094d\u092f",
        "Zip/Postal Code": "\u091c\u093c\u093f\u092a / \u092a\u094b\u0938\u094d\u091f\u0932 \u0915\u094b\u0921",
        "Phone": "\u092b\u093c\u094b\u0928",
        "Phone Number": "\u092b\u093c\u094b\u0928 \u0928\u0902\u092c\u0930",
        "Mobile": "\u092e\u094b\u092c\u093e\u0907\u0932",
        "Mobile Number": "\u092e\u094b\u092c\u093e\u0907\u0932 \u0928\u0902\u092c\u0930",
        "Email": "\u0908\u092e\u0947\u0932",
        "Email Address": "\u0908\u092e\u0947\u0932 \u092a\u0924\u093e",
        "Signature": "\u0939\u0938\u094d\u0924\u093e\u0915\u094d\u0937\u0930",
        "Father Name": "\u092a\u093f\u0924\u093e \u0915\u093e \u0928\u093e\u092e",
        "Mother Name": "\u092e\u093e\u0924\u093e \u0915\u093e \u0928\u093e\u092e",
        "Occupation": "\u0935\u094d\u092f\u0935\u0938\u093e\u092f",
        "Aadhaar": "\u0906\u0927\u093e\u0930",
        "Licence Type": "\u0932\u093e\u0907\u0938\u0947\u0902\u0938 \u092a\u094d\u0930\u0915\u093e\u0930",
        "Annual Income": "\u0935\u093e\u0930\u094d\u0937\u093f\u0915 \u0906\u092f",
        "Roll Number": "\u0930\u094b\u0932 \u0928\u0902\u092c\u0930",
        "ERP ID": "\u0908\u0906\u0930\u092a\u0940 \u0906\u0908\u0921\u0940",
        "Class": "\u0915\u0915\u094d\u0937\u093e",
        "School": "\u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f",
        "Annual Income": "\u0935\u093e\u0930\u094d\u0937\u093f\u0915 \u0906\u092f",
    },
    "Bengali": {
        "Full Name": "\u09aa\u09c2\u09b0\u09cd\u09a3 \u09a8\u09be\u09ae",
        "Name": "\u09a8\u09be\u09ae",
        "Date of Birth": "\u099c\u09a8\u09cd\u09ae \u09a4\u09be\u09b0\u09bf\u0996",
        "Date": "\u09a4\u09be\u09b0\u09bf\u0996",
        "Street Address": "\u09b0\u09be\u09b8\u09cd\u09a4\u09be\u09b0 \u09a0\u09bf\u0995\u09be\u09a8\u09be",
        "Address": "\u09a0\u09bf\u0995\u09be\u09a8\u09be",
        "City": "\u09b6\u09b9\u09b0",
        "State/Province": "\u09b0\u09be\u099c\u09cd\u09af",
        "Zip/Postal Code": "\u099c\u09bf\u09aa / \u09aa\u09cb\u09b8\u09cd\u099f\u09be\u09b2 \u0995\u09cb\u09a1",
        "Phone": "\u09ab\u09cb\u09a8",
        "Phone Number": "\u09ab\u09cb\u09a8 \u09a8\u09ae\u09cd\u09ac\u09b0",
        "Mobile": "\u09ae\u09cb\u09ac\u09be\u0987\u09b2",
        "Mobile Number": "\u09ae\u09cb\u09ac\u09be\u0987\u09b2 \u09a8\u09ae\u09cd\u09ac\u09b0",
        "Email": "\u0987\u09ae\u09c7\u09b2",
        "Email Address": "\u0987\u09ae\u09c7\u09b2 \u09a0\u09bf\u0995\u09be\u09a8\u09be",
        "Signature": "\u09b8\u09cd\u09ac\u09be\u0995\u09cd\u09b7\u09b0",
        "Father Name": "\u09aa\u09bf\u09a4\u09be\u09b0 \u09a8\u09be\u09ae",
        "Mother Name": "\u09ae\u09be\u09df\u09c7\u09b0 \u09a8\u09be\u09ae",
        "Occupation": "\u09aa\u09c7\u09b6\u09be",
        "Aadhaar": "\u0986\u09a7\u09be\u09b0",
        "Licence Type": "\u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8\u09c7\u09b0 \u09a7\u09b0\u09a8",
        "Annual Income": "\u09ac\u09be\u09b0\u09cd\u09b7\u09bf\u0995 \u0986\u09af\u09bc",
        "Roll Number": "\u09b0\u09cb\u09b2 \u09a8\u09ae\u09cd\u09ac\u09b0",
        "ERP ID": "\u0987\u0986\u09b0\u09aa\u09bf \u0986\u0987\u09a1\u09bf",
        "Class": "\u09b6\u09cd\u09b0\u09c7\u09a3\u09bf",
        "School": "\u09b8\u09cd\u0995\u09c1\u09b2",
    },
    "Tamil": {
        "Full Name": "\u0bae\u0bc1\u0bb4\u0bc1 \u0baa\u0bc6\u0baf\u0bb0\u0bcd",
        "Name": "\u0baa\u0bc6\u0baf\u0bb0\u0bcd",
        "Date of Birth": "\u0baa\u0bbf\u0bb1\u0ba8\u0bcd\u0ba4 \u0ba4\u0bc7\u0ba4\u0bbf",
        "Date": "\u0ba4\u0bc7\u0ba4\u0bbf",
        "Street Address": "\u0ba4\u0bc6\u0bb0\u0bc1 \u0bae\u0bc1\u0b95\u0bb5\u0bb0\u0bbf",
        "Address": "\u0bae\u0bc1\u0b95\u0bb5\u0bb0\u0bbf",
        "City": "\u0ba8\u0b95\u0bb0\u0bae\u0bcd",
        "State/Province": "\u0bae\u0bbe\u0ba8\u0bbf\u0bb2\u0bae\u0bcd",
        "Zip/Postal Code": "\u0b9c\u0bbf\u0baa\u0bcd / \u0b85\u0b9e\u0bcd\u0b9a\u0bb2\u0bcd \u0b95\u0bcb\u0b9f\u0bc1",
        "Phone": "\u0ba4\u0bca\u0bb2\u0bc8\u0baa\u0bc7\u0b9a\u0bbf",
        "Phone Number": "\u0ba4\u0bca\u0bb2\u0bc8\u0baa\u0bc7\u0b9a\u0bbf \u0b8e\u0ba3\u0bcd",
        "Mobile": "\u0bae\u0bca\u0baa\u0bc8\u0bb2\u0bcd",
        "Mobile Number": "\u0bae\u0bca\u0baa\u0bc8\u0bb2\u0bcd \u0b8e\u0ba3\u0bcd",
        "Email": "\u0bae\u0bbf\u0ba9\u0bcd\u0ba9\u0b9e\u0bcd\u0b9a\u0bb2\u0bcd",
        "Email Address": "\u0bae\u0bbf\u0ba9\u0bcd\u0ba9\u0b9e\u0bcd\u0b9a\u0bb2\u0bcd \u0bae\u0bc1\u0b95\u0bb5\u0bb0\u0bbf",
        "Signature": "\u0b95\u0bc8\u0baf\u0bca\u0baa\u0bcd\u0baa\u0bae\u0bcd",
        "Father Name": "\u0ba4\u0ba8\u0bcd\u0ba4\u0bc8\u0baf\u0bbf\u0ba9\u0bcd \u0baa\u0bc6\u0baf\u0bb0\u0bcd",
        "Mother Name": "\u0ba4\u0bbe\u0baf\u0bbf\u0ba9\u0bcd \u0baa\u0bc6\u0baf\u0bb0\u0bcd",
        "Occupation": "\u0ba4\u0bca\u0bb4\u0bbf\u0bb2\u0bcd",
        "Aadhaar": "\u0b86\u0ba4\u0bbe\u0bb0\u0bcd",
        "Licence Type": "\u0b89\u0bb0\u0bbf\u0bae \u0bb5\u0b95\u0bc8",
        "Annual Income": "\u0b86\u0ba3\u0bcd\u0b9f\u0bc1 \u0bb5\u0bb0\u0bc1\u0bae\u0bbe\u0ba9\u0bae\u0bcd",
        "Roll Number": "\u0bb0\u0bcb\u0bb2\u0bcd \u0b8e\u0ba3\u0bcd",
        "ERP ID": "\u0b88\u0b86\u0bb0\u0bcd\u0baa\u0bbf \u0b90\u0b9f\u0bbf",
        "Class": "\u0bb5\u0b95\u0bc1\u0baa\u0bcd\u0baa\u0bc1",
        "School": "\u0baa\u0bb3\u0bcd\u0bb3\u0bbf",
    },
    "Marathi": {
        "Full Name": "\u092a\u0942\u0930\u094d\u0923 \u0928\u093e\u0935",
        "Name": "\u0928\u093e\u0935",
        "Date of Birth": "\u091c\u0928\u094d\u092e\u0924\u093e\u0930\u0940\u0916",
        "Date": "\u0924\u093e\u0930\u0940\u0916",
        "Street Address": "\u0930\u0938\u094d\u0924\u094d\u092f\u093e\u091a\u093e \u092a\u0924\u094d\u0924\u093e",
        "Address": "\u092a\u0924\u094d\u0924\u093e",
        "City": "\u0936\u0939\u0930",
        "State/Province": "\u0930\u093e\u091c\u094d\u092f",
        "Zip/Postal Code": "\u091d\u093f\u092a / \u092a\u094b\u0938\u094d\u091f\u0932 \u0915\u094b\u0921",
        "Phone": "\u092b\u094b\u0928",
        "Phone Number": "\u092b\u094b\u0928 \u0928\u0902\u092c\u0930",
        "Mobile": "\u092e\u094b\u092c\u093e\u0907\u0932",
        "Mobile Number": "\u092e\u094b\u092c\u093e\u0907\u0932 \u0928\u0902\u092c\u0930",
        "Email": "\u0908\u092e\u0947\u0932",
        "Email Address": "\u0908\u092e\u0947\u0932 \u092a\u0924\u093e",
        "Signature": "\u0938\u0939\u0940",
        "Father Name": "\u0935\u0921\u093f\u0932\u093e\u0902\u091a\u0947 \u0928\u093e\u0935",
        "Mother Name": "\u0906\u0908\u091a\u0947 \u0928\u093e\u0935",
        "Occupation": "\u0935\u094d\u092f\u0935\u0938\u093e\u092f",
        "Aadhaar": "\u0906\u0927\u093e\u0930",
        "Licence Type": "\u092a\u0930\u0935\u093e\u0928\u093e \u092a\u094d\u0930\u0915\u093e\u0930",
        "Annual Income": "\u0935\u093e\u0930\u094d\u0937\u093f\u0915 \u0909\u0924\u094d\u092a\u0928\u094d\u0928",
        "Roll Number": "\u0930\u094b\u0932 \u0928\u0902\u092c\u0930",
        "ERP ID": "\u0908\u0906\u0930\u092a\u0940 \u0906\u092f\u0921\u0940",
        "Class": "\u0935\u0930\u094d\u0917",
        "School": "\u0936\u093e\u0933\u093e",
    },
}


def translate_label(label: str, language: str) -> str:
    if language == "English":
        return label
    return TRANSLATIONS.get(language, {}).get(label, label)


def translate_fields(fields: List[Dict[str, str]], language: str) -> List[Dict[str, str]]:
    translated_fields = []
    for field in fields:
        original_label = field.get("original_label") or field.get("label") or "Field"
        translated_field = dict(field)
        translated_field["label"] = translate_label(original_label, language)
        translated_field["original_label"] = original_label
        translated_field["type"] = field.get("type", "text")
        translated_fields.append(translated_field)
    return translated_fields
