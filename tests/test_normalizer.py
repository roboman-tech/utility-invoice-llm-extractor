from src.normalizer import (
    normalize_date,
    normalize_number,
    normalize_unit,
    normalize_utility_type,
)


def test_normalize_multilingual_dates() -> None:
    assert normalize_date("12/03/2026") == "2026-03-12"
    assert normalize_date("7 abril 2026") == "2026-04-07"
    assert normalize_date("19 mars 2026") == "2026-03-19"


def test_normalize_numbers_with_locale_separators() -> None:
    assert normalize_number("1,242 kWh") == 1242.0
    assert normalize_number("1.536,5") == 1536.5
    assert normalize_number("41,80 EUR") == 41.80


def test_normalize_units() -> None:
    assert normalize_unit("kwh") == "kWh"
    assert normalize_unit("therm") == "therms"
    assert normalize_unit("m³") == "m3"
    assert normalize_unit("gal") == "gallons"


def test_normalize_utility_type_multilingual_aliases() -> None:
    assert normalize_utility_type("electricidad") == "electricity"
    assert normalize_utility_type("gaz naturel") == "gas"
    assert normalize_utility_type("agua potable") == "water"
