from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


@dataclass(frozen=True)
class LoadedDocument:
    source_file: str
    path: Path
    text: str


def load_documents(input_dir: Path) -> list[LoadedDocument]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    documents: list[LoadedDocument] = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        text = extract_text(path)
        if text.strip():
            documents.append(
                LoadedDocument(source_file=path.name, path=path, text=text.strip())
            )

    return documents


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    raise ValueError(f"Unsupported file extension: {path.suffix}")


def _extract_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    page_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(page_text)
