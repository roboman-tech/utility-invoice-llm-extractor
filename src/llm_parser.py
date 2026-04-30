from __future__ import annotations

import json
import os
from typing import Any

from src.mock_parser import get_mock_extraction
from src.rule_extractor import extract_rule_based_fields
from src.schemas import InvoiceExtraction


class InvoiceParser:
    def parse(
        self, invoice_text: str, source_file: str, language_hint: str | None
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockInvoiceParser(InvoiceParser):
    """Deterministic parser used for local tests and checked-in sample output."""

    def parse(
        self, invoice_text: str, source_file: str, language_hint: str | None
    ) -> dict[str, Any]:
        try:
            return get_mock_extraction(source_file)
        except KeyError:
            fallback = extract_rule_based_fields(invoice_text)
            fallback.setdefault("language", language_hint)
            fallback.setdefault("confidence", None)
            return fallback


class DeepSeekInvoiceParser(InvoiceParser):
    def __init__(self, api_key: str, model: str = "deepseek-v4-flash") -> None:
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek extraction.")
        self.model = model

        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    @classmethod
    def from_env(cls) -> "DeepSeekInvoiceParser":
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        return cls(api_key=api_key, model=model)

    def parse(
        self, invoice_text: str, source_file: str, language_hint: str | None
    ) -> dict[str, Any]:
        prompt = build_extraction_prompt(invoice_text, source_file, language_hint)
        content = None
        for _ in range(2):
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=1200,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            if content:
                break

        if not content:
            raise ValueError("DeepSeek returned empty content for JSON extraction.")
        parsed = json.loads(content)
        return InvoiceExtraction.model_validate(parsed).model_dump()


SYSTEM_INSTRUCTION = """
You are a careful utility invoice data extraction assistant.
Extract only facts supported by the provided invoice text.
Return valid JSON only, matching the requested schema.
Use null for missing or ambiguous fields.
Do not invent service addresses, dates, usage, or vendors.
""".strip()


def build_extraction_prompt(
    invoice_text: str, source_file: str, language_hint: str | None
) -> str:
    return f"""
Extract utility invoice fields from the text below and return a JSON object.

Source file: {source_file}
Detected language hint: {language_hint or "unknown"}

Rules:
- Handle English, Spanish, French, or other invoice languages.
- Normalize dates to YYYY-MM-DD when the date is clear.
- Classify utility_type as exactly one of: electricity, gas, water, or null.
- Put only the numeric usage value in usage_amount.
- Put the unit separately in usage_unit, preserving standard units such as kWh, therms, gallons, or m3.
- If multiple usage numbers appear, choose the total consumption for the billing period.
- Return null when a field is not shown or is too ambiguous.
- Set language to a short language code if you can infer it.
- Set confidence from 0.0 to 1.0 based on evidence quality.

Required JSON format:
{{
  "vendor_name": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "service_address": "string or null",
  "utility_type": "electricity | gas | water | null",
  "usage_amount": 123.45,
  "usage_unit": "string or null",
  "billing_period_start": "YYYY-MM-DD or null",
  "billing_period_end": "YYYY-MM-DD or null",
  "language": "en | es | fr | other code | null",
  "confidence": 0.0
}}

Invoice text:
```text
{invoice_text}
```
""".strip()
