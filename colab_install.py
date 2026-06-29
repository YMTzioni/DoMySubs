"""התקנת תלויות מותאמת ל-Google Colab."""

from __future__ import annotations

import subprocess
import sys


def _run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def install_colab_deps(restart_hint: bool = True) -> None:
    """
    סדר התקנה מותאם ל-Colab:
    1. numpy + pillow יציבים
    2. הסרת torchvision
    3. whisperx ושאר החבילות
    """
    py = sys.executable

    _run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    _run([py, "-m", "pip", "install", "-q", "numpy>=2.1.0,<2.3.0", "--force-reinstall"])
    _run([py, "-m", "pip", "install", "-q", "pillow>=8.0,<12.0"])

    subprocess.call(
        [py, "-m", "pip", "uninstall", "-y", "torchvision"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _run([py, "-m", "pip", "install", "-q", "-U", "whisperx"])
    _run([py, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"])

    if restart_hint:
        print(
            "\n⚠️  אם מופיעה שגיאת numpy (_blas_supports_fpe):\n"
            "    Runtime → Restart session\n"
            "    ואז הרץ שוב רק תאים 4 → 5 → 6 (בלי תא 1–3)\n"
        )

    import numpy as np

    print(f"numpy {np.__version__}")

    from domysubs.compat_transformers import verify_whisperx_import

    print("✓", verify_whisperx_import())


if __name__ == "__main__":
    install_colab_deps()
