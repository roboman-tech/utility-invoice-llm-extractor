from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any

from dateutil import parser

from src.schemas import InvoiceRecord


MONTH_REPLACEMENTS = {
    "enero": "january",
    "febrero": "february",
    "marzo": "march",
    "abril": "april",
    "mayo": "may",
    "junio": "june",
    "julio": "july",
    "agosto": "august",
    "septiembre": "september",
    "setiembre": "september",
    "octubre": "october",
    "noviembre": "november",
    "diciembre": "december",
    "janvier": "january",
    "fevrier": "february",
    "février": "february",
    "mars": "march",
    "avril": "april",
    "mai": "may",
    "juin": "june",
    "juillet": "july",
    "aout": "august",
    "août": "august",
    "septembre": "september",
    "octobre": "october",
    "novembre": "november",
    "decembre": "december",
    "décembre": "december",
}

UNIT_ALIASES = {
    "kwh": "kWh",
    "kw/h": "kWh",
    "kilowatt-hour": "kWh",
    "kilowatt hours": "kWh",
    "therm": "therms",
    "therms": "therms",
    "gal": "gallons",
    "gallon": "gallons",
    "gallons": "gallons",
    "galones": "gallons",
    "m3": "m3",
    "m^3": "m3",
    "m³": "m3",
    "cubic meters": "m3",
    "metros cubicos": "m3",
    "metros cúbicos": "m3",
}

UTILITY_ALIASES = {
    "electric": "electricity",
    "electricity": "electricity",
    "electricidad": "electricity",
    "energia": "electricity",
    "energía": "electricity",
    "water": "water",
    "agua": "water",
    "eau": "water",
    "gas": "gas",
    "gaz": "gas",
}


def normalize_record(raw: dict[str, Any], source_file: str, language_hint: str | None) -> InvoiceRecord:
    language = clean_string(raw.get("language")) or language_hint
    dayfirst = infer_dayfirst(
        [
            raw.get("invoice_date"),
            raw.get("billing_period_start"),
            raw.get("billing_period_end"),
        ],
        language,
        raw.get("service_address"),
    )
    normalized = {
        "source_file": source_file,
        "vendor_name": clean_string(raw.get("vendor_name")),
        "invoice_date": normalize_date(raw.get("invoice_date"), dayfirst=dayfirst),
        "service_address": clean_string(raw.get("service_address")),
        "utility_type": normalize_utility_type(raw.get("utility_type")),
        "usage_amount": normalize_number(raw.get("usage_amount")),
        "usage_unit": normalize_unit(raw.get("usage_unit")),
        "billing_period_start": normalize_date(raw.get("billing_period_start"), dayfirst=dayfirst),
        "billing_period_end": normalize_date(raw.get("billing_period_end"), dayfirst=dayfirst),
        "language": language,
        "confidence": normalize_confidence(raw),
    }
    normalized["confidence"] = adjust_confidence(normalized, raw.get("confidence"))
    return InvoiceRecord.model_validate(normalized)


def clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return re.sub(r"\s+", " ", text)


def normalize_date(value: Any, dayfirst: bool | None = None) -> str | None:
    text = clean_string(value)
    if not text:
        return None

    text = _replace_non_english_months(text)
    if dayfirst is None:
        dayfirst = bool(re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$", text))
    try:
        parsed = parser.parse(text, dayfirst=dayfirst, fuzzy=True)
    except (ValueError, OverflowError, TypeError):
        return None
    return date(parsed.year, parsed.month, parsed.day).isoformat()


def infer_dayfirst(values: list[Any], language: str | None, service_address: Any = None) -> bool:
    default = False if looks_like_us_address(service_address) else language in {"es", "fr"}
    saw_first_over_12 = False
    saw_second_over_12 = False

    for value in values:
        text = clean_string(value)
        if not text:
            continue
        match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", text)
        if not match:
            continue
        first = int(match.group(1))
        second = int(match.group(2))
        saw_first_over_12 = saw_first_over_12 or first > 12
        saw_second_over_12 = saw_second_over_12 or second > 12

    if saw_second_over_12 and not saw_first_over_12:
        return False
    if saw_first_over_12 and not saw_second_over_12:
        return True
    return default


def looks_like_us_address(value: Any) -> bool:
    text = clean_string(value)
    if not text:
        return False
    return re.search(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", text) is not None


def _replace_non_english_months(text: str) -> str:
    output = text
    lowered_ascii = strip_accents(text.lower())
    for source, target in MONTH_REPLACEMENTS.items():
        source_ascii = strip_accents(source.lower())
        if source_ascii in lowered_ascii:
            output = re.sub(source, target, output, flags=re.IGNORECASE)
            output = re.sub(source_ascii, target, output, flags=re.IGNORECASE)
    return output


def strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def normalize_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = clean_string(value)
    if not text:
        return None
    match = re.search(r"[-+]?\d[\d.,\s]*", text)
    if not match:
        return None

    token = match.group(0).replace(" ", "")
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        decimal_comma = re.search(r",\d{1,2}$", token) is not None
        token = token.replace(",", "." if decimal_comma else "")

    try:
        return float(token)
    except ValueError:
        return None


def normalize_unit(value: Any) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    key = strip_accents(text.lower()).replace("³", "3")
    key = re.sub(r"\s+", " ", key)
    return UNIT_ALIASES.get(key, text)


def normalize_utility_type(value: Any) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    key = strip_accents(text.lower())
    for alias, canonical in UTILITY_ALIASES.items():
        if alias in key:
            return canonical
    return None


def normalize_confidence(raw: dict[str, Any]) -> float | None:
    value = raw.get("confidence")
    if value is None:
        return None
    amount = normalize_number(value)
    if amount is None:
        return None
    if amount > 1 and amount <= 100:
        amount = amount / 100
    return max(0.0, min(1.0, amount))


def adjust_confidence(record: dict[str, Any], model_confidence: Any) -> float:
    required_like_fields = [
        "vendor_name",
        "invoice_date",
        "utility_type",
        "usage_amount",
        "usage_unit",
        "billing_period_start",
        "billing_period_end",
    ]
    missing = sum(1 for field in required_like_fields if record.get(field) in (None, ""))
    present = len(required_like_fields) - missing
    evidence_confidence = 0.35 + (present / len(required_like_fields)) * 0.5

    model_score = normalize_confidence({"confidence": model_confidence})
    confidence = evidence_confidence if model_score is None else max(model_score, evidence_confidence)

    if record.get("service_address") in (None, ""):
        confidence -= 0.03

    return round(max(0.0, min(1.0, confidence)), 2)
