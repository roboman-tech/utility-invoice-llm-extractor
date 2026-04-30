from src.normalizer import normalize_record
from src.rule_extractor import merge_with_rule_based_extraction


METRO_TEXT = """
METRO ELECTRIC POWER
Utility Invoice / Fatura de servicos
Customer Name / Nome do cliente: Amelia Brooks
Service Address / Endereco do servico: 9714 Riverbend Ct, Phoenix, AZ 85016
Bill Date / Data da fatura: 03/26/2026
Service Period / Periodo de servico: 02/17/2026 to 03/22/2026
Usage / Consumo: 726.0 kWh
"""


def test_rule_based_fallback_recovers_labeled_metro_fields() -> None:
    raw = {
        "vendor_name": "METRO ELECTRIC POWER",
        "invoice_date": None,
        "service_address": None,
        "utility_type": None,
        "usage_amount": None,
        "usage_unit": None,
        "billing_period_start": None,
        "billing_period_end": None,
        "language": "en",
        "confidence": 0,
    }

    merged = merge_with_rule_based_extraction(raw, METRO_TEXT)
    record = normalize_record(merged, "metro.txt", "en")

    assert record.invoice_date == "2026-03-26"
    assert record.service_address == "9714 Riverbend Ct, Phoenix, AZ 85016"
    assert record.utility_type == "electricity"
    assert record.usage_amount == 726.0
    assert record.usage_unit == "kWh"
    assert record.billing_period_start == "2026-02-17"
    assert record.billing_period_end == "2026-03-22"
    assert record.confidence == 0.85
