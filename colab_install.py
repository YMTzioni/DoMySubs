"""התקנת תלויות מותאמת ל-Google Colab."""

from __future__ import annotations

import subprocess
import sys


def install_colab_deps() -> None:
    py = sys.executable

    subprocess.check_call([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    subprocess.call(
        [py, "-m", "pip", "uninstall", "-y", "torchvision"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call([py, "-m", "pip", "install", "-q", "-U", "whisperx"])
    subprocess.check_call([py, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"])

    print(
        "\n⚠️  מומלץ: Runtime → Restart session\n"
        "    ואז הרץ: from domysubs.compat_transformers import verify_whisperx_import; print(verify_whisperx_import())\n"
    )

    from domysubs.compat_transformers import verify_whisperx_import

    print("✓", verify_whisperx_import())


if __name__ == "__main__":
    install_colab_deps()
