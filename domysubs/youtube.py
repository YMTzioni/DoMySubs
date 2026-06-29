from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from domysubs.config import WORK_DIR

logger = logging.getLogger(__name__)

YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+",
    re.IGNORECASE,
)


def is_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_RE.match(url.strip()))


def download_youtube(url: str, output_dir: Path | None = None) -> str:
    """הורדת אודיו מיוטיוב. מחזיר נתיב לקובץ."""
    out_dir = output_dir or WORK_DIR / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    template = str(out_dir / "%(title).80s_%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-x",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "-o",
        template,
        url,
    ]

    logger.info("Downloading: %s", url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    # מצא את הקובץ שהורד
    wav_files = sorted(out_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
    if wav_files:
        return str(wav_files[0])

    # fallback - חפש כל אודיו
    for ext in ("m4a", "mp3", "webm", "opus", "ogg"):
        files = sorted(out_dir.glob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            return str(files[0])

    raise FileNotFoundError("לא נמצא קובץ שהורד מיוטיוב")


def download_youtube_video(url: str, output_dir: Path | None = None) -> str:
    """הורדת וידאו מיוטיוב (לחילוץ אודיו מקומי)."""
    out_dir = output_dir or WORK_DIR / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    template = str(out_dir / "%(title).80s_%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o",
        template,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    for ext in ("mp4", "mkv", "webm"):
        files = sorted(out_dir.glob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            return str(files[0])

    raise FileNotFoundError("לא נמצא וידאו שהורד מיוטיוב")
