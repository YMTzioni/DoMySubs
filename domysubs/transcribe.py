from __future__ import annotations

import gc
import logging
from typing import Callable

import torch

from domysubs.config import Settings

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]


def _detect_device(requested: str) -> str:
    if requested == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def transcribe_audio(
    audio_path: str,
    settings: Settings,
    language: str | None = None,
    progress: ProgressCallback | None = None,
) -> tuple[list[dict], str]:
    """תמלול קובץ אודיו עם WhisperX. מחזיר segments וקוד שפה."""
    import whisperx

    device = _detect_device(settings.device)
    compute_type = settings.compute_type if device == "cuda" else "int8"

    if progress:
        progress("טוען מודל WhisperX...", 5)

    model = whisperx.load_model(
        settings.model,
        device,
        compute_type=compute_type,
        language=language,
    )

    if progress:
        progress("טוען אודיו...", 15)

    audio = whisperx.load_audio(audio_path)

    if progress:
        progress("מתמלל...", 25)

    transcribe_kwargs: dict = {"batch_size": settings.batch_size}
    if language:
        transcribe_kwargs["language"] = language

    result = model.transcribe(audio, **transcribe_kwargs)
    detected_language = result.get("language", language or "en")

    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    if progress:
        progress(f"מיישר טיימסטמפים ({detected_language})...", 60)

    try:
        align_model, metadata = whisperx.load_align_model(
            language_code=detected_language,
            device=device,
        )
        result = whisperx.align(
            result["segments"],
            align_model,
            metadata,
            audio,
            device,
            return_char_alignments=False,
        )
        del align_model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
    except Exception as exc:
        logger.warning("Alignment failed, using raw segments: %s", exc)

    if progress:
        progress("תמלול הושלם", 90)

    return result["segments"], detected_language


def segments_to_cues(segments: list[dict]) -> list:
    from domysubs.srt import SubtitleCue

    cues = []
    for i, seg in enumerate(segments, start=1):
        text = seg.get("text", "").strip()
        if not text:
            continue
        cues.append(
            SubtitleCue(
                index=i,
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=text,
            )
        )
    return cues
