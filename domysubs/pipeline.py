from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from domysubs.audio import prepare_audio
from domysubs.config import WORK_DIR, Settings, get_settings
from domysubs.srt import SubtitleCue, read_srt, save_srt
from domysubs.transcribe import segments_to_cues, transcribe_audio
from domysubs.translate import detect_language, translate_cues
from domysubs.youtube import download_youtube, is_youtube_url

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]


def _noop_progress(msg: str, pct: float) -> None:
    logger.info("[%d%%] %s", int(pct), msg)


def _output_path(name: str = "subtitles_he") -> Path:
    out_dir = WORK_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return out_dir / f"{name}_{ts}.srt"


def process_media(
    input_path: str,
    settings: Settings | None = None,
    source_language: str | None = None,
    skip_translation: bool = False,
    progress: ProgressCallback | None = None,
) -> tuple[str, list[SubtitleCue], str]:
    """
    עיבוד קובץ וידאו/אודיו:
    תמלול → תרגום לעברית → SRT
  """
    settings = settings or get_settings()
    progress = progress or _noop_progress

    progress("מכין אודיו...", 5)
    audio_path = prepare_audio(input_path)

    segments, detected_lang = transcribe_audio(
        audio_path,
        settings,
        language=source_language,
        progress=progress,
    )

    cues = segments_to_cues(segments)
    src_lang = source_language or detected_lang

    if skip_translation or src_lang == "he":
        progress("שומר כתוביות...", 95)
    else:
        progress(f"מתרגם מ-{src_lang} לעברית...", 90)
        cues = translate_cues(cues, source_lang=src_lang, target_lang="he", progress=progress)

    out_path = _output_path()
    save_srt(cues, str(out_path))
    progress("הושלם!", 100)

    return str(out_path), cues, src_lang


def process_youtube(
    url: str,
    settings: Settings | None = None,
    source_language: str | None = None,
    skip_translation: bool = False,
    progress: ProgressCallback | None = None,
) -> tuple[str, list[SubtitleCue], str]:
    """הורדה מיוטיוב → תמלול → תרגום → SRT."""
    progress = progress or _noop_progress

    if not is_youtube_url(url):
        raise ValueError("קישור יוטיוב לא תקין")

    progress("מוריד מיוטיוב...", 2)
    audio_path = download_youtube(url)

    return process_media(
        audio_path,
        settings=settings,
        source_language=source_language,
        skip_translation=skip_translation,
        progress=progress,
    )


def process_srt(
    srt_path: str,
    source_language: str = "auto",
    progress: ProgressCallback | None = None,
) -> tuple[str, list[SubtitleCue]]:
    """תרגום קובץ SRT קיים לעברית."""
    progress = progress or _noop_progress

    progress("קורא SRT...", 10)
    cues = read_srt(srt_path)

    if source_language == "auto" and cues:
        sample = " ".join(c.text for c in cues[:5])
        source_language = detect_language(sample)
        progress(f"שפה מזוהה: {source_language}", 20)

    progress("מתרגם לעברית...", 30)
    translated = translate_cues(
        cues,
        source_lang=source_language,
        target_lang="he",
        progress=progress,
    )

    out_path = _output_path("translated_he")
    save_srt(translated, str(out_path))
    progress("הושלם!", 100)

    return str(out_path), translated


def process_input(
    source: str,
    settings: Settings | None = None,
    source_language: str | None = None,
    skip_translation: bool = False,
    progress: ProgressCallback | None = None,
) -> tuple[str, list[SubtitleCue], str | None]:
    """
    נקודת כניסה אחת - מזהה סוג קלט ומעבד.
    מחזיר: (נתיב SRT, cues, שפת מקור)
    """
    source = source.strip()

    if is_youtube_url(source):
        path, cues, lang = process_youtube(
            source,
            settings=settings,
            source_language=source_language,
            skip_translation=skip_translation,
            progress=progress,
        )
        return path, cues, lang

    path_obj = Path(source)
    if path_obj.suffix.lower() == ".srt":
        out_path, cues = process_srt(source, source_language or "auto", progress)
        return out_path, cues, source_language

    path, cues, lang = process_media(
        source,
        settings=settings,
        source_language=source_language,
        skip_translation=skip_translation,
        progress=progress,
    )
    return path, cues, lang
