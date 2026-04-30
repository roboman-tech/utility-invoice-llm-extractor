from __future__ import annotations

import re
from typing import Any


FIELD_PATTERNS = {
    "service_address": re.compile(
        r"(?:service address|endereco do servico|direccion de servicio|direccion de servico|"
        r"adresse de service)"
        r"\s*(?:/[^:]+)?\s*:\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
    "invoice_date": re.compile(
        r"(?:bill date|invoice date|data da fatura|fecha de factura|fecha de facturacion|"
        r"date de facture|date de facturation)"
        r"\s*(?:/[^:]+)?\s*:\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
}

PERIOD_PATTERN = re.compile(
    r"(?:service period|periodo de servico|billing period|periodo de facturacion|"
    r"periodo de servicio|periode de consommation|periode de service)"
    r"\s*(?:/[^:]+)?\s*:\s*(?P<start>.+?)\s+(?:to|through|al|au|-)\s+(?P<end>.+)",
    re.IGNORECASE,
)

USAGE_PATTERN = re.compile(
    r"(?:usage|consumo|total energy used|consommation)"
    r"\s*(?:/[^:]+)?\s*:\s*(?P<amount>[-+]?\d[\d,.\s]*)\s*(?P<unit>kwh|therms?|gallons?|gal|m3)\b",
    re.IGNORECASE,
)


def merge_with_rule_based_extraction(
    llm_result: dict[str, Any], invoice_text: str
) -> dict[str, Any]:
    fallback = extract_rule_based_fields(invoice_text)
    merged = dict(llm_result)
    for field, value in fallback.items():
        if is_missing(merged.get(field)):
            merged[field] = value
    return merged


def extract_rule_based_fields(invoice_text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    lines = invoice_text.splitlines()

    vendor = extract_vendor(lines)
    if vendor:
        fields["vendor_name"] = vendor

    for field, pattern in FIELD_PATTERNS.items():
        match = pattern.search(invoice_text)
        if match:
            fields[field] = match.group("value").strip()

    period = PERIOD_PATTERN.search(invoice_text)
    if period:
        fields["billing_period_start"] = period.group("start").strip()
        fields["billing_period_end"] = period.group("end").strip()

    usage = USAGE_PATTERN.search(invoice_text)
    if usage:
        fields["usage_amount"] = usage.group("amount").strip()
        fields["usage_unit"] = usage.group("unit").strip()

    utility_type = infer_utility_type(fields.get("usage_unit"), invoice_text)
    if utility_type:
        fields["utility_type"] = utility_type

    return fields


def extract_vendor(lines: list[str]) -> str | None:
    for line in lines[:8]:
        cleaned = line.strip(" =-")
        if not cleaned or ":" in cleaned:
            continue
        if re.search(r"invoice|factura|fatura|statement", cleaned, re.IGNORECASE):
            continue
        if re.search(r"electric|energy|water|utility|gas|gaz|agua", cleaned, re.IGNORECASE):
            return cleaned
    return None


def infer_utility_type(unit: Any, invoice_text: str) -> str | None:
    text = f"{unit or ''} {invoice_text}".lower()
    if "kwh" in text or "electric" in text:
        return "electricity"
    if "therm" in text or re.search(r"\bgas\b|\bgaz\b", text):
        return "gas"
    if "gallon" in text or " m3" in text or "water" in text or "agua" in text:
        return "water"
    return None


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "null", "none", "n/a"}:
        return True
    return False
