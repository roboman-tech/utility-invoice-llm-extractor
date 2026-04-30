from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from src.csv_writer import write_csv
from src.document_loader import load_documents
from src.llm_parser import DeepSeekInvoiceParser, MockInvoiceParser
from src.normalizer import normalize_record
from src.preprocessor import InvoicePreprocessor
from src.rule_extractor import merge_with_rule_based_extraction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured utility invoice data into CSV."
    )
    parser.add_argument("--input-dir", default="data/input", help="Folder of .txt/.pdf invoices.")
    parser.add_argument(
        "--output",
        default="data/output/extracted_invoices.csv",
        help="CSV output path.",
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use deterministic sample extractions instead of calling DeepSeek.",
    )
    parser.add_argument(
        "--allow-mock-fallback",
        action="store_true",
        help="Use mock parser if DEEPSEEK_API_KEY is not set.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    documents = load_documents(input_dir)
    preprocessor = InvoicePreprocessor()
    parser = build_parser(args.mock_llm, args.allow_mock_fallback)

    records = []
    for document in documents:
        prepared = preprocessor.run(document.text)
        raw_extraction = parser.parse(
            prepared.text,
            source_file=document.source_file,
            language_hint=prepared.language_hint,
        )
        raw_extraction = merge_with_rule_based_extraction(raw_extraction, prepared.text)
        records.append(
            normalize_record(
                raw_extraction,
                source_file=document.source_file,
                language_hint=prepared.language_hint,
            )
        )

    write_csv(records, output_path)
    print(f"Wrote {len(records)} invoice rows to {output_path}")


def build_parser(use_mock: bool, allow_mock_fallback: bool):
    if use_mock:
        return MockInvoiceParser()
    if os.getenv("DEEPSEEK_API_KEY"):
        return DeepSeekInvoiceParser.from_env()
    if allow_mock_fallback:
        return MockInvoiceParser()
    raise RuntimeError(
        "DEEPSEEK_API_KEY is not set. Add it to .env or run with --mock-llm for the sample fixture."
    )


if __name__ == "__main__":
    main()
