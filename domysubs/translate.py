from __future__ import annotations

import logging
import time
from typing import Callable

from deep_translator import GoogleTranslator

from domysubs.srt import SubtitleCue

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]

# מיפוי קודי שפה נפוצים ל-Google Translate
LANG_MAP = {
    "he": "iw",  # Google משתמש ב-iw לעברית
    "iw": "iw",
}


def _to_google_lang(code: str) -> str:
    return LANG_MAP.get(code, code)


def detect_language(text: str) -> str:
    """זיהוי שפה בסיסי לפי טקסט."""
    if not text.strip():
        return "auto"
    try:
        return GoogleTranslator(source="auto", target="en").detect(text[:500])
    except Exception:
        return "auto"


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "he",
) -> str:
    if not text.strip():
        return text

    src = "auto" if source_lang in ("auto", "") else _to_google_lang(source_lang)
    tgt = _to_google_lang(target_lang)

    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except Exception as exc:
        logger.warning("Translation failed for chunk: %s", exc)
        return text


def translate_cues(
    cues: list[SubtitleCue],
    source_lang: str = "auto",
    target_lang: str = "he",
    progress: ProgressCallback | None = None,
    batch_pause: float = 0.1,
) -> list[SubtitleCue]:
    """תרגום רשימת כתוביות לעברית תוך שמירה על טיימסטמפים."""
    translated: list[SubtitleCue] = []
    total = len(cues)

    for i, cue in enumerate(cues):
        if progress and total:
            pct = 90 + (i / total) * 10
            progress(f"מתרגם {i + 1}/{total}...", pct)

        hebrew_text = translate_text(cue.text, source_lang, target_lang)
        translated.append(
            SubtitleCue(
                index=cue.index,
                start=cue.start,
                end=cue.end,
                text=hebrew_text,
            )
        )
        if batch_pause:
            time.sleep(batch_pause)

    return translated
