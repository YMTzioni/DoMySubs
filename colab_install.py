"""התקנת תלויות מותאמת ל-Google Colab."""

from __future__ import annotations

import subprocess
import sys


def _run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def install_colab_deps() -> None:
  """מתקין ומתקן גרסאות שבורות ב-Colab (transformers / torchvision)."""
  _run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", "pip"])

  # torchvision גורם לשגיאות import ב-Colab עם WhisperX
  subprocess.call(
      [sys.executable, "-m", "pip", "uninstall", "-y", "torchvision"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )

  _run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"])
  _run([
      sys.executable, "-m", "pip", "install", "-q",
      "transformers>=4.48.0,<4.52.0",
      "--force-reinstall",
  ])

  from transformers import Pipeline  # noqa: F401
  import whisperx  # noqa: F401

  import transformers
  print(f"✓ התקנה הושלמה | transformers {transformers.__version__} | whisperx OK")


if __name__ == "__main__":
    install_colab_deps()
