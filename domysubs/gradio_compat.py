"""תאימות Gradio — עובד ב-Colab (4.x) ובמחשב (6.x)."""

from __future__ import annotations

import gradio as gr

from domysubs.ui_theme import CUSTOM_CSS, studio_theme


def blocks_kwargs() -> dict:
    """theme/css תמיד ב-Blocks — לא ב-launch (שובר ב-Colab)."""
    base = {"title": "DoMySubs Studio"}
    try:
        base["theme"] = studio_theme()
        base["css"] = CUSTOM_CSS
    except Exception:
        pass
    return base


def launch_app(
    app: gr.Blocks,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    share: bool = False,
) -> None:
    # לעולם לא מעבירים theme/css ל-launch — גורם לשגיאה ב-Gradio 4/5
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
    )
