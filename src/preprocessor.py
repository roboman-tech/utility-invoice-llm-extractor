from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from langdetect import DetectorFactory, LangDetectException, detect

    DetectorFactory.seed = 7
except Exception:  # pragma: no cover - import availability is environment-specific
    detect = None
    LangDetectException = Exception


KEYWORD_PATTERN = re.compile(
    r"("
    r"invoice|statement|factura|facture|fecha|date|issued|emision|"
    r"service address|direccion|adresse|suministro|"
    r"billing period|billing cycle|periodo|periode|desde|hasta|through|"
    r"electric|electricidad|energia|energy|kwh|"
    r"gas|gaz|therm|"
    r"water|agua|gallons|galones|m3|consumo|consumption|usage"
    r")",
    re.IGNORECASE,
)

FIELD_LABEL_PATTERN = re.compile(
    r"("
    r"customer name|nome do cliente|"
    r"service address|endereco do servico|direccion de servicio|adresse de service|"
    r"account number|numero da conta|"
    r"invoice number|numero da fatura|"
    r"bill date|invoice date|data da fatura|fecha de factura|date de facture|"
    r"due date|data de vencimento|"
    r"service period|periodo de servico|billing period|periodo de facturacion|"
    r"amount due|valor devido|"
    r"previous reading|current reading|usage|consumo"
    r")",
    re.IGNORECASE,
)

BOILERPLATE_PATTERN = re.compile(
    r"("
    r"quick links|click on|home page|sign up|payment information|"
    r"please do not include|by mail|in person|paying your bill|"
    r"about your utility bill|this area provides|description of what you will find|"
    r"various options|water conservation|customer service information"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PreprocessedDocument:
    text: str
    language_hint: str | None


class InvoicePreprocessor:
    """Reduces an invoice to the highest-signal lines before the LLM call."""

    def __init__(self, max_chars: int = 6000) -> None:
        self.max_chars = max_chars

    def run(self, raw_text: str) -> PreprocessedDocument:
        cleaned = normalize_whitespace(raw_text)
        language_hint = detect_language(cleaned)
        candidate_text = select_candidate_lines(cleaned)
        if len(candidate_text) > self.max_chars:
            candidate_text = candidate_text[: self.max_chars]
        return PreprocessedDocument(text=candidate_text, language_hint=language_hint)


def normalize_whitespace(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        compacted = re.sub(r"[ \t]+", " ", line).strip()
        if compacted:
            lines.append(compacted)
    return "\n".join(lines)


def select_candidate_lines(text: str, context_window: int = 1) -> str:
    lines = text.splitlines()
    if not lines:
        return ""

    scores = [score_line(line) for line in lines]
    preferred_start, preferred_end = best_dense_window(scores, window_size=70)
    selected: set[int] = set(range(preferred_start, preferred_end))

    for idx, line in enumerate(lines):
        if scores[idx] >= 4 or KEYWORD_PATTERN.search(line):
            start = max(0, idx - context_window)
            end = min(len(lines), idx + context_window + 1)
            selected.update(range(start, end))

    ordered = order_selected_lines(
        lines, selected, preferred_range=(preferred_start, preferred_end)
    )
    return "\n".join(ordered)


def score_line(line: str) -> int:
    score = 0
    if FIELD_LABEL_PATTERN.search(line):
        score += 10
    if re.search(r"\b\d[\d,.\s]*\s*(kwh|therms?|gallons?|gal|m3)\b", line, re.IGNORECASE):
        score += 8
    if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", line):
        score += 4
    if re.search(r"utility invoice|fatura de servicos|factura|facture", line, re.IGNORECASE):
        score += 4
    if KEYWORD_PATTERN.search(line):
        score += 2
    if BOILERPLATE_PATTERN.search(line):
        score -= 6
    return score


def best_dense_window(scores: list[int], window_size: int) -> tuple[int, int]:
    if len(scores) <= window_size:
        return 0, len(scores)

    best_start = 0
    best_score = float("-inf")
    for start in range(0, len(scores) - window_size + 1):
        window_score = sum(max(score, 0) for score in scores[start : start + window_size])
        if window_score > best_score:
            best_score = window_score
            best_start = start
    return best_start, best_start + window_size


def order_selected_lines(
    lines: list[str], selected: set[int], preferred_range: tuple[int, int]
) -> list[str]:
    preferred_start, preferred_end = preferred_range
    preferred = [
        lines[idx]
        for idx in range(preferred_start, preferred_end)
        if idx in selected and not BOILERPLATE_PATTERN.search(lines[idx])
    ]
    supplemental = [
        lines[idx]
        for idx in sorted(selected)
        if not (preferred_start <= idx < preferred_end)
        and not BOILERPLATE_PATTERN.search(lines[idx])
    ]
    return preferred + supplemental


def detect_language(text: str) -> str | None:
    if detect is None:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
