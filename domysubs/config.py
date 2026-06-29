import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORK_DIR = Path(os.getenv("DOMYSUBS_WORK_DIR", "workspace"))
WORK_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    device: str = os.getenv("DOMYSUBS_DEVICE", "cpu")
    model: str = os.getenv("DOMYSUBS_MODEL", "large-v2")
    batch_size: int = int(os.getenv("DOMYSUBS_BATCH_SIZE", "8"))
    compute_type: str = os.getenv("DOMYSUBS_COMPUTE_TYPE", "int8")
    hf_token: str | None = os.getenv("HF_TOKEN")
    target_language: str = "he"
    max_line_width: int = 42
    max_line_count: int = 2


def get_settings() -> Settings:
    return Settings()


def settings_from_recommendation(rec) -> Settings:
    """בונה Settings מהמלצת סריקת חומרה."""
    s = rec.settings
    base = get_settings()
    return Settings(
        device=s.device,
        model=s.model,
        batch_size=s.batch_size,
        compute_type=s.compute_type,
        hf_token=base.hf_token,
        target_language=base.target_language,
        max_line_width=base.max_line_width,
        max_line_count=base.max_line_count,
    )
