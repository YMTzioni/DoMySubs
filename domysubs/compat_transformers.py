"""תיקון ייבוא transformers.Pipeline עבור WhisperX ב-Colab."""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)

_PATCHED = False


def ensure_transformers_pipeline() -> None:
    """
    WhisperX עושה: from transformers import Pipeline
    ב-Colab הייבוא נכשל לעיתים בגלל torchvision/PIL — מתקנים ידנית.
    """
    global _PATCHED
    if _PATCHED:
        return

    import transformers

    try:
        from transformers import Pipeline  # noqa: F401

        _PATCHED = True
        return
    except ImportError:
        logger.debug("transformers.Pipeline not in __init__, attempting patch")

    try:
        importlib.import_module("transformers.pipelines")
        from transformers import Pipeline  # noqa: F401

        _PATCHED = True
        return
    except ImportError:
        pass

    for module_path in (
        "transformers.pipelines.base",
        "transformers.pipelines.pipeline",
    ):
        try:
            module = importlib.import_module(module_path)
            pipeline_cls = getattr(module, "Pipeline", None)
            if pipeline_cls is not None:
                transformers.Pipeline = pipeline_cls
                _PATCHED = True
                logger.info("Patched transformers.Pipeline from %s", module_path)
                return
        except Exception as exc:
            logger.debug("Patch attempt failed for %s: %s", module_path, exc)

    raise ImportError(
        "לא ניתן לטעון transformers.Pipeline ל-WhisperX.\n"
        "ב-Colab הרץ:\n"
        "  !pip uninstall -y torchvision\n"
        "  !pip install -U pillow whisperx\n"
        "ואז הפעל מחדש את הריצה."
    )


def verify_whisperx_import() -> str:
    """בדיקת ייבוא — מחזיר גרסאות לתצוגה."""
    ensure_transformers_pipeline()
    import transformers
    import whisperx

    return f"transformers {transformers.__version__} | whisperx OK"
