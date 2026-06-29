from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from domysubs.config import WORK_DIR

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wma"}


def is_video(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def extract_audio(video_path: str, output_dir: Path | None = None) -> str:
    """חילוץ אודיו מוידאו ל-WAV באמצעות ffmpeg."""
    src = Path(video_path)
    out_dir = output_dir or WORK_DIR / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{src.stem}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(out_path),
    ]

    logger.info("Extracting audio: %s", video_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return str(out_path)


def prepare_audio(input_path: str) -> str:
    """מכין קובץ אודיו לתמלול - מחזיר נתיב ישיר או מחולץ."""
    path = Path(input_path)
    if is_audio(str(path)):
        return str(path)
    if is_video(str(path)):
        return extract_audio(str(path))
    raise ValueError(f"סוג קובץ לא נתמך: {path.suffix}")
