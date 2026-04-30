from src.normalizer import adjust_confidence
from src.preprocessor import InvoicePreprocessor


def test_preprocessor_prioritizes_invoice_block_after_long_boilerplate() -> None:
    boilerplate = "\n".join(
        [
            "To receive this statement via email, click on Sign up for E-Billing under Quick Links.",
            "To sign up for monthly automatic payments, click on Payment Information.",
            "ABOUT YOUR UTILITY BILL",
            "This area provides account number, service address, service period, billing date, and due date.",
            "PAYING YOUR BILL",
        ]
        * 45
    )
    invoice = """
METRO ELECTRIC POWER
Utility Invoice / Fatura de servicos
Customer Name / Nome do cliente: Amelia Brooks
Service Address / Endereco do servico: 9714 Riverbend Ct, Phoenix, AZ 85016
Account Number / Numero da conta: 7554991273
Invoice Number / Numero da fatura: INV-202600175
Bill Date / Data da fatura: 03/26/2026
Due Date / Data de vencimento: 04/18/2026
Service Period / Periodo de servico: 02/17/2026 to 03/22/2026
Amount Due / Valor devido: $225.19
Meter / Medidor: EL9634362
Previous Reading / Leitura anterior: 79,521
Current Reading / Leitura atual: 80,247
Usage / Consumo: 726.0 kWh
Billing Days: 34
"""

    prepared = InvoicePreprocessor(max_chars=1600).run(f"{boilerplate}\n{invoice}")

    assert "METRO ELECTRIC POWER" in prepared.text
    assert "Service Address / Endereco do servico: 9714 Riverbend Ct" in prepared.text
    assert "Bill Date / Data da fatura: 03/26/2026" in prepared.text
    assert "Service Period / Periodo de servico: 02/17/2026 to 03/22/2026" in prepared.text
    assert "Usage / Consumo: 726.0 kWh" in prepared.text
    assert "Quick Links" not in prepared.text


def test_confidence_does_not_collapse_to_zero_when_fields_are_present() -> None:
    record = {
        "vendor_name": "METRO ELECTRIC POWER",
        "invoice_date": "2026-03-26",
        "service_address": "9714 Riverbend Ct, Phoenix, AZ 85016",
        "utility_type": "electricity",
        "usage_amount": 726.0,
        "usage_unit": "kWh",
        "billing_period_start": "2026-02-17",
        "billing_period_end": "2026-03-22",
    }

    assert adjust_confidence(record, 0) == 0.85
