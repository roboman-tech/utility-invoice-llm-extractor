import csv
from pathlib import Path

from src.csv_writer import write_csv
from src.document_loader import load_documents
from src.llm_parser import MockInvoiceParser
from src.normalizer import normalize_record
from src.preprocessor import InvoicePreprocessor


KNOWN_SAMPLE_FILES = [
    "invoice_en_electricity.txt",
    "invoice_en_missing_address.txt",
    "invoice_es_electricity_layout.txt",
    "invoice_es_water.txt",
    "invoice_fr_gas.txt",
]

MINIMAL_SAMPLE_TEXT = {
    "invoice_en_electricity.txt": "BrightGrid Electric\nInvoice Date: March 5, 2026\nTotal Energy Used: 1,242 kWh",
    "invoice_en_missing_address.txt": "North Coast Water Utility\nInvoice issued: 2026-04-02\nMetered consumption: 6,750 gallons",
    "invoice_es_electricity_layout.txt": "Compania Electrica Sur\nFecha emision 7 abril 2026\nEnergia consumida: 1.536,5 kWh",
    "invoice_es_water.txt": "Aguas del Valle\nFecha de factura: 12/03/2026\nConsumo total: 24 m3",
    "invoice_fr_gas.txt": "Gaz Municipal de Lyon\nDate de facture: 19 mars 2026\nConsommation: 63 therms",
}


def test_mock_pipeline_writes_all_rows(tmp_path: Path) -> None:
    input_dir = _copy_known_samples(tmp_path)
    docs = load_documents(input_dir)
    preprocessor = InvoicePreprocessor()
    parser = MockInvoiceParser()

    records = []
    for doc in docs:
        prepared = preprocessor.run(doc.text)
        raw = parser.parse(prepared.text, doc.source_file, prepared.language_hint)
        records.append(normalize_record(raw, doc.source_file, prepared.language_hint))

    output_path = tmp_path / "extracted.csv"
    write_csv(records, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "BrightGrid Electric" in content
    assert "Aguas del Valle" in content
    assert "Gaz Municipal de Lyon" in content
    assert len(content.strip().splitlines()) == 6


def test_mock_pipeline_matches_expected_ground_truth(tmp_path: Path) -> None:
    input_dir = _copy_known_samples(tmp_path)
    docs = load_documents(input_dir)
    preprocessor = InvoicePreprocessor()
    parser = MockInvoiceParser()
    output_path = tmp_path / "extracted.csv"

    records = []
    for doc in docs:
        prepared = preprocessor.run(doc.text)
        raw = parser.parse(prepared.text, doc.source_file, prepared.language_hint)
        records.append(normalize_record(raw, doc.source_file, prepared.language_hint))

    write_csv(records, output_path)

    assert _read_csv(output_path) == _read_csv(Path("data/expected/expected_invoices.csv"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _copy_known_samples(tmp_path: Path) -> Path:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for filename in KNOWN_SAMPLE_FILES:
        (input_dir / filename).write_text(MINIMAL_SAMPLE_TEXT[filename], encoding="utf-8")
    return input_dir
