"""LLM prompts for extracting information from German medical bills.

This module contains prompt templates for different extraction tasks.
Prompts are designed to work with German medical terminology and formatting.
"""

# Phase 1: Basic extraction prompt (practitioner, date, total amount)
BASIC_EXTRACTION_PROMPT = """You are analyzing a German medical bill (Arztrechnung/Rechnung). Extract the following information and return it as valid JSON.

Return ONLY the JSON object, no additional text or explanations.

Required JSON structure:
{{
  "practitioner_name": "Full name of doctor or clinic",
  "practitioner_type": "One of: Arzt, Zahnarzt, Heilpraktiker, Krankenhaus, Labor, Apotheke, Sonstige",
  "bill_date": "Date in YYYY-MM-DD format",
  "bill_number": "Invoice/bill number if present",
  "total_amount": "Total amount in EUR as decimal number (e.g., 29.49)",
  "currency": "EUR"
}}

Important guidelines:
- practitioner_type must be exactly one of: Arzt, Zahnarzt, Heilpraktiker, Krankenhaus, Labor, Apotheke, Sonstige
- If information cannot be determined, use null for that field
- bill_date must be in ISO format: YYYY-MM-DD (e.g., 2024-03-15)
- total_amount should be the final total amount (Gesamtbetrag/Summe/Total)
- Look for keywords like: Gesamtbetrag, Summe, Endbetrag, Total, Rechnungsbetrag
- For practitioner_type, map common terms:
  - "Arzt", "Ärztin", "Doktor", "Dr. med." → Arzt
  - "Zahnarzt", "Zahnärztin" → Zahnarzt
  - "Heilpraktiker", "Heilpraktikerin" → Heilpraktiker
  - "Klinik", "Krankenhaus", "Hospital" → Krankenhaus
  - "Labor", "Laboratorium" → Labor
  - "Apotheke" → Apotheke
  - If unclear → Sonstige

Bill text:
{bill_text}

JSON response:"""


# Future: Phase 3 line item extraction prompt
LINE_ITEM_EXTRACTION_PROMPT = """You are analyzing a German medical bill (Arztrechnung). Extract all line items from the bill.

Return ONLY valid JSON, no additional text.

Required JSON structure:
{{
  "practitioner_info": {{
    "practitioner_name": "Full name",
    "practitioner_type": "Arzt/Zahnarzt/etc",
    "bill_date": "YYYY-MM-DD",
    "bill_number": "Invoice number",
    "total_amount": "Total EUR as decimal",
    "currency": "EUR"
  }},
  "line_items": [
    {{
      "position": "Line item number if present",
      "date": "Service date in YYYY-MM-DD",
      "goa_code": "GOÄ or EBM code (e.g., '1', '5', '250')",
      "description": "Service description in German",
      "quantity": "Number as decimal (e.g., 1, 2.5)",
      "unit_price": "Price per unit in EUR",
      "total_price": "Total for this line in EUR",
      "factor": "GOÄ factor if applicable (e.g., 2.3, 1.0)"
    }}
  ]
}}

Important:
- Extract all line items present in the bill
- Look for GOÄ codes (Gebührenordnung für Ärzte)
- If field cannot be determined, use null
- Dates in YYYY-MM-DD format

Bill text:
{bill_text}

JSON response:"""


def get_prompt(extraction_type: str, bill_text: str) -> str:
    """Get formatted prompt for extraction type.

    Args:
        extraction_type: Type of extraction ("basic" or "line_items")
        bill_text: Text extracted from PDF

    Returns:
        Formatted prompt ready to send to LLM

    Raises:
        ValueError: If extraction_type is not recognized
    """
    prompts = {
        "basic": BASIC_EXTRACTION_PROMPT,
        "line_items": LINE_ITEM_EXTRACTION_PROMPT,
    }

    if extraction_type not in prompts:
        raise ValueError(
            f"Unknown extraction type: {extraction_type}. "
            f"Must be one of: {', '.join(prompts.keys())}"
        )

    return prompts[extraction_type].format(bill_text=bill_text)
