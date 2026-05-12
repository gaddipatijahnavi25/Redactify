from enum import Enum
from pathlib import Path
import mimetypes


class FileType(str, Enum):
    TEXT = "text"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
TEXT_EXTENSIONS = {".txt", ".md", ".log"}


def detect_file_type(filename: str) -> FileType:
    ext = Path(filename).suffix.lower()

    if ext == ".csv":
        return FileType.CSV
    if ext == ".json":
        return FileType.JSON
    if ext == ".pdf":
        return FileType.PDF
    if ext in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if ext in TEXT_EXTENSIONS:
        return FileType.TEXT

    mime, _ = mimetypes.guess_type(filename)
    if mime:
        if mime.startswith("image/"):
            return FileType.IMAGE
        if mime == "application/pdf":
            return FileType.PDF
        if "text" in mime:
            return FileType.TEXT

    return FileType.UNKNOWN
