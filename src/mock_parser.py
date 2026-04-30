from __future__ import annotations


MOCK_EXTRACTIONS: dict[str, dict[str, object]] = {
    "invoice_en_electricity.txt": {
        "vendor_name": "BrightGrid Electric",
        "invoice_date": "March 5, 2026",
        "service_address": "1842 Pine Street, Denver, CO 80203",
        "utility_type": "electricity",
        "usage_amount": "1,242",
        "usage_unit": "kWh",
        "billing_period_start": "February 1, 2026",
        "billing_period_end": "February 28, 2026",
        "language": "en",
        "confidence": 0.96,
    },
    "invoice_es_water.txt": {
        "vendor_name": "Aguas del Valle",
        "invoice_date": "12/03/2026",
        "service_address": "Calle Mayor 18, Piso 2, 28013 Madrid",
        "utility_type": "agua",
        "usage_amount": "24",
        "usage_unit": "m³",
        "billing_period_start": "01/02/2026",
        "billing_period_end": "28/02/2026",
        "language": "es",
        "confidence": 0.95,
    },
    "invoice_fr_gas.txt": {
        "vendor_name": "Gaz Municipal de Lyon",
        "invoice_date": "19 mars 2026",
        "service_address": "22 Rue Victor Hugo, 69002 Lyon",
        "utility_type": "gaz",
        "usage_amount": 63,
        "usage_unit": "therm",
        "billing_period_start": "15 fevrier 2026",
        "billing_period_end": "14 mars 2026",
        "language": "fr",
        "confidence": 0.95,
    },
    "invoice_en_missing_address.txt": {
        "vendor_name": "North Coast Water Utility",
        "invoice_date": "2026-04-02",
        "service_address": None,
        "utility_type": "water",
        "usage_amount": "6,750",
        "usage_unit": "gallons",
        "billing_period_start": "2026-03-01",
        "billing_period_end": "2026-03-31",
        "language": "en",
        "confidence": 0.91,
    },
    "invoice_es_electricity_layout.txt": {
        "vendor_name": "Compania Electrica Sur",
        "invoice_date": "7 abril 2026",
        "service_address": "Avenida Libertad 450, 41001 Sevilla",
        "utility_type": "electricidad",
        "usage_amount": "1.536,5",
        "usage_unit": "kwh",
        "billing_period_start": "01/03/2026",
        "billing_period_end": "31/03/2026",
        "language": "es",
        "confidence": 0.94,
    },
}


def get_mock_extraction(source_file: str) -> dict[str, object]:
    try:
        return MOCK_EXTRACTIONS[source_file]
    except KeyError as exc:
        raise KeyError(f"No mock extraction is defined for {source_file}") from exc
