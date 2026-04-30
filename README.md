# Utility Invoice Processing with DeepSeek

Lightweight batch pipeline for extracting structured utility invoice fields from text-based invoices and writing a clean CSV.

The implementation intentionally keeps the architecture simple: deterministic document loading and preprocessing, one JSON-mode DeepSeek extraction call per invoice, then local validation/normalization before CSV output.

## What It Does

- Loads `.txt` and text-based `.pdf` invoices from `data/input/`
- Preprocesses raw text into invoice-relevant candidate lines
- Detects a language hint with `langdetect`
- Calls DeepSeek in JSON mode with a strict extraction prompt
- Applies a rule-based fallback for clearly labeled fields if the model misses them
- Normalizes dates, usage amounts, utility types, and units
- Writes one CSV row per invoice to `data/output/extracted_invoices.csv`
- Includes a deterministic `--mock-llm` mode for tests and reproducible sample output

## Project Structure

```text
data/
  input/                 sample English, Spanish, and French invoices
  expected/              manually validated ground truth CSV
  output/                generated CSV output
src/
  document_loader.py     txt/pdf text extraction
  preprocessor.py        whitespace cleanup, language hint, candidate line filtering
  llm_parser.py          DeepSeek JSON-mode parser
  rule_extractor.py      deterministic fallback for obvious labels
  normalizer.py          post-LLM validation and normalization
  schemas.py             Pydantic schemas and CSV field order
  main.py                CLI entry point
tests/
  test_normalizer.py
  test_pipeline_mock.py
```

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `DEEPSEEK_API_KEY` in `.env`.

On Windows PowerShell, use `copy .env.example .env` instead of `cp`.

The DeepSeek parser uses the OpenAI Python SDK with `base_url="https://api.deepseek.com"` and JSON mode via `response_format={"type": "json_object"}`. References:

- https://api-docs.deepseek.com/
- https://api-docs.deepseek.com/guides/json_mode/

## Run With DeepSeek

```bash
python -m src.main
```

Optional paths:

```bash
python -m src.main --input-dir data/input --output data/output/extracted_invoices.csv
```

## Run Reproducible Local Demo

Use this when you do not want to spend API calls or when validating the checked-in sample files:

```bash
python -m src.main --mock-llm --output data/output/extracted_invoices.csv
```

The generated output is also copied at `sample_output.csv`.

## Assumptions

- Invoices are text-based. OCR is out of scope because the prompt explicitly says text is already available.
- Utility type is normalized to `electricity`, `gas`, or `water`.
- Dates are normalized to `YYYY-MM-DD` when parseable; otherwise they become blank in CSV.
- Missing fields are stored as `None` internally and blank in CSV.
- The LLM should extract facts only from the provided invoice text. Post-processing code handles formatting cleanup rather than asking the model to do every small transformation.
- Mock invoices are acceptable sample inputs for the take-home and include English, Spanish, and French variation.

## Multilingual Strategy

The pipeline normalizes all invoices into one English CSV schema regardless of source language. `langdetect` provides a language hint, and the DeepSeek prompt explicitly asks the model to handle multilingual labels such as `factura`, `fecha`, `periodo`, `consumo`, `facture`, `adresse`, and `consommation`.

The preprocessor is multilingual too: it keeps lines around invoice, address, period, usage, unit, gas, electricity, and water keywords in English, Spanish, and French. This reduces prompt noise before DeepSeek sees the document.

## Validation and Normalization

After the LLM returns JSON, the pipeline fills missing obvious fields from labels such as `Bill Date`, `Service Address`, `Service Period`, and `Usage`, then applies deterministic cleanup:

- Dates: parsed into ISO format, including Spanish and French month names
- Date format: infers month-first vs day-first from the invoice dates and US address patterns
- Numbers: handles `1,242`, `1.536,5`, and values with units attached
- Units: maps variants like `kwh`, `therm`, `m3`, and `gal`
- Utility type: maps multilingual aliases like `electricidad`, `agua`, and `gaz`
- Confidence: uses model confidence, then lightly penalizes missing important fields

## Testing and Evaluation Approach

Run:

```bash
python -m pytest -q
```

### How I Validated Accuracy

I used a small manually labeled ground-truth file at `data/expected/expected_invoices.csv`. For each sample invoice, I inspected the source text and recorded the expected value for every output field:

- `vendor_name`
- `invoice_date`
- `service_address`
- `utility_type`
- `usage_amount`
- `usage_unit`
- `billing_period_start`
- `billing_period_end`
- `language`
- `confidence`

The end-to-end mock pipeline test compares generated CSV rows against this expected CSV. For live DeepSeek runs, I would use the same expected file as the baseline and calculate field-level accuracy:

```text
field_accuracy = correct_extracted_fields / total_expected_fields
row_accuracy = rows_with_all_required_fields_correct / total_rows
missing_field_rate = expected_fields_returned_blank / total_expected_fields
hallucination_rate = fields_populated_when source text does not support the value
```

For numeric fields, I would compare normalized values instead of raw strings. For example, `1,242 kWh`, `1242`, and `1,242.0` should all be evaluated as the same usage amount after normalization. For dates, I compare ISO-normalized values like `2026-03-26`.

### Test Cases and Edge Cases Considered

The current sample set and tests cover:

- Date normalization for English-style numeric dates, Spanish month names, and French month names
- Locale-aware numeric parsing
- Unit normalization
- Multilingual utility type mapping
- End-to-end mock pipeline output against manually validated ground truth in `data/expected/expected_invoices.csv`
- Missing fields, such as an invoice with no service address
- Different invoice layouts and label names
- English, Spanish, French, Portuguese-style bilingual labels, and mixed-language invoices
- Unit variations such as `kWh`, `therm`, `therms`, `gallons`, `gal`, and `m3`
- Long boilerplate text before the actual invoice fields
- Bilingual labels where the content still uses US-style dates, such as `03/26/2026`
- Low or zero model confidence even when extracted evidence is present

The long-boilerplate case is important because real utility bills often include payment instructions, conservation notices, and back-of-statement explanations before or after the actual billing table. The preprocessor is tested to prioritize the dense invoice block instead of blindly truncating from the beginning.

### Automated Tests Implemented

Automated tests are included under `tests/`:

- `test_normalizer.py`: validates date, number, unit, and utility type normalization
- `test_preprocessor.py`: checks that the preprocessor keeps the real invoice block when noisy boilerplate appears first
- `test_rule_extractor.py`: verifies deterministic fallback extraction for obvious labels like `Bill Date`, `Service Address`, `Service Period`, and `Usage`
- `test_pipeline_mock.py`: runs the full deterministic pipeline and compares output against ground truth

The mock parser exists so the test suite is stable, fast, and does not depend on API availability or model variability. The live LLM path should be evaluated separately with a fixed invoice set and saved outputs.

### Performance and Reliability Metrics

For this take-home, I focused on correctness and robustness. If running the live DeepSeek pipeline, I would track:

- Extraction accuracy by field, especially dates, service address, usage amount, and billing period
- End-to-end latency per invoice
- Prompt/input character count after preprocessing
- Estimated token usage and API cost per invoice
- JSON parse failure rate
- Schema validation failure rate
- Fallback usage rate, meaning how often rule-based extraction filled a missing LLM field
- Confidence calibration, checking whether low-confidence rows actually contain more errors

These metrics would help answer whether preprocessing is improving accuracy and cost. For example, if fallback usage is high for billing periods, that may indicate the prompt needs improvement or the billing-period labels should be handled more deterministically.

### How I Would Improve Testing With More Time

With more time, I would add a lightweight evaluation script such as `scripts/evaluate.py` that:

- Runs the live DeepSeek extraction on a fixed labeled dataset
- Writes a comparison report by invoice and by field
- Separates exact-match, normalized-match, missing, and hallucinated values
- Reports latency and token/cost estimates
- Stores failed examples for regression testing

I would also expand the labeled dataset to include scanned/OCR-like noisy text, multi-page PDFs, invoices with multiple meters, water plus sewer on the same bill, ambiguous service periods, missing usage units, and more languages. For production, I would add human review thresholds: for example, route invoices to review when required fields are missing, confidence is below a threshold, or normalized dates are inconsistent.
