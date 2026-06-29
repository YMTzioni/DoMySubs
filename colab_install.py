"""התקנת תלויות מותאמת ל-Google Colab."""

from __future__ import annotations

import subprocess
import sys


def _run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def install_colab_deps() -> None:
    _run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", "pip", "pillow"])

    subprocess.call(
        [sys.executable, "-m", "pip", "uninstall", "-y", "torchvision"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _run([sys.executable, "-m", "pip", "install", "-q", "-U", "whisperx"])
    _run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"])

    from domysubs.compat_transformers import verify_whisperx_import

    print("✓", verify_whisperx_import())


if __name__ == "__main__":
    install_colab_deps()
