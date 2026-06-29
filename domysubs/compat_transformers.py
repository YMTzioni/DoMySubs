"""תיקוני ייבוא WhisperX / transformers ל-Colab."""

from __future__ import annotations

import importlib
import logging
import site
import sys
import sysconfig
from pathlib import Path

logger = logging.getLogger(__name__)

_PREPARED = False


def _whisperx_asr_paths() -> list[Path]:
    roots: list[str] = []
    try:
        roots.extend(site.getsitepackages())
    except Exception:
        pass
    purelib = sysconfig.get_path("purelib")
    if purelib:
        roots.append(purelib)

    return [Path(root) / "whisperx" / "asr.py" for root in roots if root]


def patch_whisperx_asr_source() -> bool:
    """
    WhisperX עושה `from transformers import Pipeline` — נכשל ב-Colab.
    מתקן את קובץ המקור ב-site-packages לייבוא ישיר.
    """
    old = "from transformers import Pipeline"
    new = "from transformers.pipelines.base import Pipeline"
    patched = False

    for asr_path in _whisperx_asr_paths():
        if not asr_path.is_file():
            continue
        content = asr_path.read_text(encoding="utf-8")
        if old not in content:
            continue
        asr_path.write_text(content.replace(old, new), encoding="utf-8")
        patched = True
        logger.info("Patched whisperx asr: %s", asr_path)

    if patched:
        for name in list(sys.modules):
            if name == "whisperx" or name.startswith("whisperx."):
                del sys.modules[name]

    return patched


def _patch_transformers_namespace() -> bool:
    import transformers

    try:
        from transformers import Pipeline  # noqa: F401

        return True
    except ImportError:
        pass

    try:
        importlib.import_module("transformers.pipelines")
        from transformers import Pipeline  # noqa: F401

        return True
    except Exception as exc:
        logger.debug("transformers.pipelines import failed: %s", exc)

    for module_path in (
        "transformers.pipelines.base",
        "transformers.pipelines.pipeline",
    ):
        try:
            module = importlib.import_module(module_path)
            pipeline_cls = getattr(module, "Pipeline", None)
            if pipeline_cls is not None:
                transformers.Pipeline = pipeline_cls
                return True
        except Exception as exc:
            logger.debug("namespace patch via %s failed: %s", module_path, exc)

    return False


def _last_import_error() -> str:
  """מחזיר את השגיאה האמיתית מאחורי transformers.pipelines."""
  errors: list[str] = []
  for target in ("transformers.pipelines", "transformers.pipelines.base"):
      try:
          importlib.import_module(target)
      except Exception as exc:
          errors.append(f"{target}: {exc}")
  return "\n".join(errors) if errors else "לא ידוע"


def prepare_whisperx_environment() -> str:
    """מכין סביבה ל-WhisperX — קורא לפני כל תמלול."""
    global _PREPARED
    if _PREPARED:
        import numpy as np
        import transformers

        return f"numpy {np.__version__} | transformers {transformers.__version__} | whisperx ready"

    patch_whisperx_asr_source()
    _patch_transformers_namespace()

    try:
        import whisperx  # noqa: F401
    except Exception as exc:
        details = _last_import_error()
        raise ImportError(
            "WhisperX לא נטען ב-Colab.\n"
            f"שגיאה: {exc}\n"
            f"פרטים:\n{details}\n\n"
            "נסה:\n"
            "  Runtime → Restart session\n"
            "  !pip uninstall -y torchvision\n"
            "  !pip install -U whisperx\n"
        ) from exc

    _PREPARED = True
    import numpy as np
    import transformers

    return f"numpy {np.__version__} | transformers {transformers.__version__} | whisperx OK"


def ensure_transformers_pipeline() -> None:
    """תאימות לאחור."""
    prepare_whisperx_environment()


def verify_whisperx_import() -> str:
    return prepare_whisperx_environment()
