#!/usr/bin/env python3
"""הפעלת הסטודיו בסביבת ענן (Colab / RunPod / HF)."""

from __future__ import annotations

import os

from domysubs.gradio_compat import launch_app
from domysubs.studio import create_app


def launch_cloud(
    host: str | None = None,
    port: int | None = None,
    share: bool | None = None,
) -> None:
    host = host or os.getenv("DOMYSUBS_HOST", "0.0.0.0")
    port = int(port or os.getenv("DOMYSUBS_PORT", "7860"))
    if share is None:
        share = os.getenv("DOMYSUBS_SHARE", "true").lower() in ("1", "true", "yes")

    if os.getenv("COLAB_RELEASE_TAG"):
        share = True
        os.environ.setdefault("DOMYSUBS_DEVICE", "cuda")
        os.environ.setdefault("DOMYSUBS_COMPUTE_TYPE", "float16")

    from domysubs.compat_transformers import prepare_whisperx_environment

    prepare_whisperx_environment()

    launch_app(
        create_app(),
        server_name=host,
        server_port=port,
        share=share,
    )


if __name__ == "__main__":
    launch_cloud()
