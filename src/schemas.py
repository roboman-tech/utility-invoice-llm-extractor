from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


UtilityType = Literal["electricity", "gas", "water"]


class InvoiceExtraction(BaseModel):
    vendor_name: str | None = Field(
        default=None, description="Utility provider or vendor name."
    )
    invoice_date: str | None = Field(
        default=None, description="Invoice issue date, ideally YYYY-MM-DD."
    )
    service_address: str | None = Field(
        default=None, description="Physical service address, if shown."
    )
    utility_type: str | None = Field(
        default=None, description="One of electricity, gas, water, or null."
    )
    usage_amount: float | None = Field(
        default=None, description="Numeric usage amount only, without units."
    )
    usage_unit: str | None = Field(
        default=None, description="Usage unit such as kWh, therms, gallons, or m3."
    )
    billing_period_start: str | None = Field(
        default=None, description="Billing period start date, ideally YYYY-MM-DD."
    )
    billing_period_end: str | None = Field(
        default=None, description="Billing period end date, ideally YYYY-MM-DD."
    )
    language: str | None = Field(
        default=None, description="Detected invoice language code such as en, es, fr."
    )
    confidence: float | None = Field(
        default=None, description="Extractor confidence from 0.0 to 1.0."
    )


class InvoiceRecord(InvoiceExtraction):
    source_file: str
    utility_type: UtilityType | None = Field(
        default=None, description="One of electricity, gas, water, or null."
    )


CSV_FIELDS = [
    "source_file",
    "vendor_name",
    "invoice_date",
    "service_address",
    "utility_type",
    "usage_amount",
    "usage_unit",
    "billing_period_start",
    "billing_period_end",
    "language",
    "confidence",
]
