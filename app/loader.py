"""Read documents from disk into plain text."""

from pathlib import Path

from pypdf import PdfReader

from .config import SUPPORTED_EXTENSIONS


def read_file(path: Path) -> str:
    """Return the text content of a .txt, .md or .pdf file."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def load_folder(folder: Path) -> dict[str, str]:
    """Load every supported file in a folder. Returns {filename: text}."""
    docs: dict[str, str] = {}
    if not folder.exists():
        return docs
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            text = read_file(path).strip()
            if text:
                docs[path.name] = text
    return docs
