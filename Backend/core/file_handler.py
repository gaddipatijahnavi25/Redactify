import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile

from core.config import settings


async def save_upload(file: UploadFile) -> Path:
    """Persist an uploaded file to the uploads directory."""
    dest = settings.upload_dir / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_text(content: str, original_name: str) -> Path:
    out = settings.output_dir / f"redacted_{original_name}"
    out.write_text(content, encoding="utf-8")
    return out


def save_csv(df: pd.DataFrame, original_name: str) -> Path:
    out = settings.output_dir / f"redacted_{original_name}"
    df.to_csv(out, index=False)
    return out


def save_json(data: Any, original_name: str) -> Path:
    out = settings.output_dir / f"redacted_{original_name}"
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out


def save_bytes(data: bytes, original_name: str) -> Path:
    out = settings.output_dir / f"redacted_{original_name}"
    out.write_bytes(data)
    return out
