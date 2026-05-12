from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI PII Redactor"
    debug: bool = True

    upload_dir: Path = BASE_DIR / "data" / "uploads"
    output_dir: Path = BASE_DIR / "data" / "outputs"

    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [
        ".txt", ".csv", ".json", ".pdf", ".png", ".jpg", ".jpeg"
    ]

    ocr_language: str = "eng"

    model_config = {"env_file": ".env"}


settings = Settings()

# Ensure directories exist on import
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
