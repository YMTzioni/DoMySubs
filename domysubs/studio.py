"""ממשק Gradio - סטודיו כתוביות DoMySubs."""

from __future__ import annotations

import logging

import gradio as gr

from domysubs.config import Settings, get_settings
from domysubs.hardware import format_scan_report, recommend_settings, scan_hardware
from domysubs.pipeline import process_input, process_srt
from domysubs.srt import write_srt
from domysubs.gradio_compat import blocks_kwargs, launch_app
from domysubs.ui_theme import FOOTER_HTML, HERO_HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGES = [
    ("זיהוי אוטומטי", None),
    ("עברית", "he"),
    ("אנגלית", "en"),
    ("ערבית", "ar"),
    ("רוסית", "ru"),
    ("צרפתית", "fr"),
    ("ספרדית", "es"),
    ("גרמנית", "de"),
    ("איטלקית", "it"),
    ("פורטוגזית", "pt"),
    ("הינדי", "hi"),
    ("סינית", "zh"),
    ("יפנית", "ja"),
    ("קוריאנית", "ko"),
    ("טורקית", "tr"),
    ("פולנית", "pl"),
    ("אוקראינית", "uk"),
]

MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]


def scan_and_recommend():
    """סורק חומרה ומחזיר הגדרות מומלצות + דוח."""
    rec = recommend_settings(scan_hardware())
    report = f'<div class="domysubs-hw-report">{_md_to_html_report(format_scan_report(rec))}</div>'
    s = rec.settings
    status = f"✓ {s.device} · {s.model} · batch {s.batch_size} · {s.compute_type}"
    return (
        report,
        status,
        s.device,
        s.model,
        s.batch_size,
        s.compute_type,
        rec.tier,
    )


def _md_to_html_report(md: str) -> str:
    """המרה בסיסית של דוח markdown ל-HTML לתצוגה מעוצבת."""
    import html
    import re

    lines = md.splitlines()
    out: list[str] = []
    in_list = False

    for line in lines:
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            text = html.escape(line[2:])
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            out.append(f"<li>{text}</li>")
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            text = html.escape(line)
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            out.append(f"<p>{text}</p>")

    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _build_settings(
    device: str,
    model: str,
    batch_size: int,
    compute_type: str,
) -> Settings:
    base = get_settings()
    return Settings(
        device=device,
        model=model,
        batch_size=int(batch_size),
        compute_type=compute_type,
        hf_token=base.hf_token,
    )


def _result_outputs(preview_limit: int = 20):
    """רכיבי פלט אחידים לכל טאב."""
    with gr.Row():
        with gr.Column(scale=1):
            out_file = gr.File(label="הורדת קובץ SRT")
        with gr.Column(scale=2):
            out_log = gr.Textbox(
                label="יומן עיבוד",
                lines=5,
                elem_classes=["mono-box"],
            )
    out_preview = gr.Textbox(
        label="תצוגה מקדימה",
        lines=10,
        elem_classes=["mono-box"],
    )
    return out_file, out_log, out_preview


def process_media_file(
    file,
    source_lang,
    device,
    model,
    batch_size,
    compute_type,
    skip_translation,
    progress=gr.Progress(),
):
    if file is None:
        return None, "העלה קובץ וידאו או אודיו", ""

    settings = _build_settings(device, model, batch_size, compute_type)
    status_log = []

    def on_progress(msg: str, pct: float):
        progress(pct / 100, desc=msg)
        status_log.append(f"[{int(pct):3d}%] {msg}")

    try:
        out_path, cues, _lang = process_input(
            file.name,
            settings=settings,
            source_language=source_lang,
            skip_translation=skip_translation,
            progress=on_progress,
        )
        preview = write_srt(cues[:20])
        if len(cues) > 20:
            preview += f"\n... ({len(cues) - 20} שורות נוספות)"
        return out_path, "\n".join(status_log), preview
    except Exception as exc:
        logger.exception("Processing failed")
        return None, f"שגיאה: {exc}", ""


def process_youtube_url(
    url,
    source_lang,
    device,
    model,
    batch_size,
    compute_type,
    skip_translation,
    progress=gr.Progress(),
):
    if not url or not url.strip():
        return None, "הזן קישור יוטיוב", ""

    settings = _build_settings(device, model, batch_size, compute_type)
    status_log = []

    def on_progress(msg: str, pct: float):
        progress(pct / 100, desc=msg)
        status_log.append(f"[{int(pct):3d}%] {msg}")

    try:
        out_path, cues, _lang = process_input(
            url.strip(),
            settings=settings,
            source_language=source_lang,
            skip_translation=skip_translation,
            progress=on_progress,
        )
        preview = write_srt(cues[:20])
        if len(cues) > 20:
            preview += f"\n... ({len(cues) - 20} שורות נוספות)"
        return out_path, "\n".join(status_log), preview
    except Exception as exc:
        logger.exception("YouTube processing failed")
        return None, f"שגיאה: {exc}", ""


def process_srt_file(
    file,
    source_lang,
    progress=gr.Progress(),
):
    if file is None:
        return None, "העלה קובץ SRT", ""

    status_log = []

    def on_progress(msg: str, pct: float):
        progress(pct / 100, desc=msg)
        status_log.append(f"[{int(pct):3d}%] {msg}")

    try:
        out_path, cues = process_srt(
            file.name,
            source_language=source_lang or "auto",
            progress=on_progress,
        )
        preview = write_srt(cues[:20])
        if len(cues) > 20:
            preview += f"\n... ({len(cues) - 20} שורות נוספות)"
        return out_path, "\n".join(status_log), preview
    except Exception as exc:
        logger.exception("SRT translation failed")
        return None, f"שגיאה: {exc}", ""


def create_app() -> gr.Blocks:
    with gr.Blocks(**blocks_kwargs()) as app:
        gr.HTML(HERO_HTML)

        with gr.Row(equal_height=False):
            # עמודת הגדרות
            with gr.Column(scale=2, min_width=300):
                with gr.Group(elem_classes=["domysubs-card"]):
                    gr.HTML('<p class="domysubs-card-title">מנוע תמלול</p>')
                    device = gr.Dropdown(
                        ["cpu", "cuda"],
                        value="cpu",
                        label="מכשיר חישוב",
                    )
                    model = gr.Dropdown(
                        MODELS,
                        value="large-v2",
                        label="מודל Whisper",
                    )
                    batch_size = gr.Slider(
                        1, 32, value=8, step=1,
                        label="גודל Batch",
                    )
                    compute_type = gr.Dropdown(
                        ["int8", "float16", "float32"],
                        value="int8",
                        label="סוג חישוב",
                    )

                with gr.Group(elem_classes=["domysubs-card"]):
                    gr.HTML('<p class="domysubs-card-title">אבחון מערכת</p>')
                    scan_btn = gr.Button(
                        "סרוק מחשב והתאם הגדרות",
                        elem_classes=["scan-btn"],
                    )
                    with gr.Row():
                        tier_label = gr.Textbox(
                            label="דרגת מערכת",
                            interactive=False,
                            elem_classes=["tier-field"],
                        )
                        scan_status = gr.Textbox(
                            label="הגדרות מומלצות",
                            interactive=False,
                            elem_classes=["status-field"],
                        )
                    hw_report = gr.HTML(
                        '<div class="domysubs-hw-report">'
                        '<p>לחץ «סרוק מחשב» לזיהוי חומרה והתאמת הגדרות אוטומטית.</p>'
                        '</div>'
                    )

            # עמודת עבודה
            with gr.Column(scale=5):
                with gr.Tabs():
                    with gr.Tab("🎬  וידאו / אודיו"):
                        with gr.Group(elem_classes=["domysubs-card"]):
                            media_file = gr.File(
                                label="גרור קובץ לכאן או לחץ לבחירה",
                                file_types=["video", "audio"],
                            )
                            with gr.Row():
                                media_lang = gr.Dropdown(
                                    LANGUAGES,
                                    value=None,
                                    label="שפת מקור",
                                )
                                media_skip = gr.Checkbox(
                                    label="ללא תרגום",
                                    value=False,
                                )
                            media_btn = gr.Button(
                                "הפק כתוביות בעברית",
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                        media_out, media_log, media_preview = _result_outputs()

                    with gr.Tab("▶️  יוטיוב"):
                        with gr.Group(elem_classes=["domysubs-card"]):
                            yt_url = gr.Textbox(
                                label="קישור יוטיוב",
                                placeholder="https://www.youtube.com/watch?v=...",
                                elem_classes=["ltr-field"],
                            )
                            with gr.Row():
                                yt_lang = gr.Dropdown(
                                    LANGUAGES,
                                    value=None,
                                    label="שפת מקור",
                                )
                                yt_skip = gr.Checkbox(
                                    label="ללא תרגום",
                                    value=False,
                                )
                            yt_btn = gr.Button(
                                "הורד, תמלל ותרגם",
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                        yt_out, yt_log, yt_preview = _result_outputs()

                    with gr.Tab("📝  תרגום SRT"):
                        with gr.Group(elem_classes=["domysubs-card"]):
                            srt_file = gr.File(
                                label="קובץ SRT קיים",
                                file_types=[".srt"],
                            )
                            srt_lang = gr.Dropdown(
                                [("זיהוי אוטומטי", "auto")] + LANGUAGES[1:],
                                value="auto",
                                label="שפת מקור",
                            )
                            srt_btn = gr.Button(
                                "תרגם לעברית",
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )
                        srt_out, srt_log, srt_preview = _result_outputs()

        gr.HTML(FOOTER_HTML)

        scan_outputs = [
            hw_report,
            scan_status,
            device,
            model,
            batch_size,
            compute_type,
            tier_label,
        ]
        scan_btn.click(scan_and_recommend, outputs=scan_outputs)
        app.load(scan_and_recommend, outputs=scan_outputs)

        media_btn.click(
            process_media_file,
            inputs=[media_file, media_lang, device, model, batch_size, compute_type, media_skip],
            outputs=[media_out, media_log, media_preview],
        )
        yt_btn.click(
            process_youtube_url,
            inputs=[yt_url, yt_lang, device, model, batch_size, compute_type, yt_skip],
            outputs=[yt_out, yt_log, yt_preview],
        )
        srt_btn.click(
            process_srt_file,
            inputs=[srt_file, srt_lang],
            outputs=[srt_out, srt_log, srt_preview],
        )

    return app


def main():
    launch_app(create_app())


if __name__ == "__main__":
    main()
