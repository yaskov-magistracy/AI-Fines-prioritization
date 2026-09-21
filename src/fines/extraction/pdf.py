import hashlib
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from fines.extraction.base import PdfPayload


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pdf(path: Path, *, with_images: bool = True) -> PdfPayload:
    """Достаёт текст постранично и, опционально, встроенные изображения."""
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    images: list[tuple[int, bytes]] = []
    if with_images:
        images = _extract_images(path)

    return PdfPayload(filename=path.name, pages=pages, images=images)


def _extract_images(path: Path) -> list[tuple[int, bytes]]:
    out: list[tuple[int, bytes]] = []
    reader = PdfReader(str(path))
    for page_no, page in enumerate(reader.pages):
        try:
            for image in page.images:
                out.append((page_no, image.data))
        except Exception:
            continue
    return out
