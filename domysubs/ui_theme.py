"""עיצוב ויזואלי מקצועי לסטודיו DoMySubs."""

from __future__ import annotations

import gradio as gr

# צבעי מותג — סטודיו כהה עם הדגשה טורקיז
ACCENT = "#2dd4bf"
ACCENT_DIM = "#14b8a6"
SURFACE = "#151d2e"
SURFACE_ALT = "#1c2738"
BORDER = "#2a3a52"
TEXT_MUTED = "#94a3b8"

CUSTOM_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
    --domysubs-accent: {ACCENT};
    --domysubs-surface: {SURFACE};
    --domysubs-border: {BORDER};
}}

/* בסיס RTL */
.gradio-container {{
    direction: rtl !important;
    font-family: 'Heebo', 'Segoe UI', sans-serif !important;
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 0 1rem 2rem !important;
}}

/* כותרת עליונה */
.domysubs-hero {{
    background: linear-gradient(135deg, #0c1220 0%, #152238 45%, #1a3040 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
}}
.domysubs-hero::before {{
    content: '';
    position: absolute;
    top: -40%;
    left: -10%;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(45, 212, 191, 0.18) 0%, transparent 70%);
    pointer-events: none;
}}
.domysubs-hero h1 {{
    margin: 0 0 0.35rem 0 !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
    letter-spacing: -0.02em;
}}
.domysubs-hero .tagline {{
    color: {TEXT_MUTED};
    font-size: 0.95rem;
    margin: 0 0 0.75rem 0;
    line-height: 1.5;
}}
.domysubs-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}}
.domysubs-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(45, 212, 191, 0.1);
    border: 1px solid rgba(45, 212, 191, 0.25);
    color: {ACCENT};
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
}}

/* כרטיסי סקשן */
.domysubs-card {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
}}
.domysubs-card-title {{
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {ACCENT};
    margin: 0 0 0.85rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid {BORDER};
}}

/* דוח חומרה */
.domysubs-hw-report {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-size: 0.88rem;
    line-height: 1.55;
    max-height: 280px;
    overflow-y: auto;
}}
.domysubs-hw-report h2 {{
    font-size: 0.95rem !important;
    color: #e2e8f0 !important;
    margin-top: 0.5rem !important;
}}
.domysubs-hw-report strong {{
    color: #cbd5e1;
}}

/* טאבים */
.tabs {{
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    overflow: hidden;
    background: {SURFACE} !important;
}}
.tab-nav {{
    background: {SURFACE_ALT} !important;
    border-bottom: 1px solid {BORDER} !important;
    padding: 0.35rem 0.5rem 0 !important;
}}
.tab-nav button {{
    font-family: 'Heebo', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0 !important;
}}
.tab-nav button.selected {{
    background: {SURFACE} !important;
    color: {ACCENT} !important;
    border-bottom: 2px solid {ACCENT} !important;
}}

/* כפתור ראשי */
.primary-btn button {{
    background: linear-gradient(135deg, {ACCENT_DIM}, {ACCENT}) !important;
    border: none !important;
    font-weight: 600 !important;
    font-family: 'Heebo', sans-serif !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}}
.primary-btn button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(45, 212, 191, 0.35) !important;
}}

/* סריקת מחשב */
.scan-btn button {{
    background: transparent !important;
    border: 1px solid {ACCENT} !important;
    color: {ACCENT} !important;
    font-weight: 600 !important;
}}
.scan-btn button:hover {{
    background: rgba(45, 212, 191, 0.08) !important;
}}

/* תצוגה מקדימה ולוג — מונוספייס */
.mono-box textarea {{
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
    font-size: 0.82rem !important;
    direction: ltr !important;
    text-align: left !important;
    background: #0d1117 !important;
    border-color: {BORDER} !important;
}}

/* קלט LTR לקישורים */
.ltr-field input {{
    direction: ltr !important;
    text-align: left !important;
}}

/* פוטר */
.domysubs-footer {{
    text-align: center;
    color: {TEXT_MUTED};
    font-size: 0.78rem;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid {BORDER};
}}
.domysubs-footer a {{
    color: {ACCENT};
    text-decoration: none;
}}
.domysubs-footer a:hover {{
    text-decoration: underline;
}}

/* שדות סטטוס */
.status-field input {{
    font-size: 0.85rem !important;
    color: {ACCENT} !important;
}}
.tier-field input {{
    font-weight: 600 !important;
}}
"""


def studio_theme() -> gr.Theme:
    return gr.themes.Base(
        primary_hue=gr.themes.colors.teal,
        secondary_hue=gr.themes.colors.slate,
        neutral_hue=gr.themes.colors.slate,
        font=gr.themes.GoogleFont("Heebo"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    ).set(
        body_background_fill="#0b0f17",
        body_background_fill_dark="#0b0f17",
        block_background_fill=SURFACE,
        block_background_fill_dark=SURFACE,
        block_border_width="1px",
        block_border_color=BORDER,
        block_border_color_dark=BORDER,
        block_label_text_color=TEXT_MUTED,
        block_label_text_color_dark=TEXT_MUTED,
        block_title_text_color="#e2e8f0",
        block_title_text_color_dark="#e2e8f0",
        block_radius="10px",
        container_radius="10px",
        input_background_fill=SURFACE_ALT,
        input_background_fill_dark=SURFACE_ALT,
        input_radius="8px",
        button_primary_background_fill=ACCENT_DIM,
        button_primary_background_fill_hover=ACCENT,
        button_primary_text_color="#0b0f17",
        button_secondary_background_fill="transparent",
        button_secondary_text_color=ACCENT,
        border_color_primary=BORDER,
        color_accent=ACCENT,
        shadow_drop="0 4px 24px rgba(0,0,0,0.25)",
    )


HERO_HTML = """
<div class="domysubs-hero">
  <h1>DoMySubs Studio</h1>
  <p class="tagline">
    סטודיו מקצועי להפקת כתוביות בעברית מכל שפה —
    וידאו, אודיו, יוטיוב או קבצי SRT.
  </p>
  <div class="domysubs-badges">
    <span class="domysubs-badge">WhisperX</span>
    <span class="domysubs-badge">תרגום אוטומטי</span>
    <span class="domysubs-badge">טיימסטמפים מדויקים</span>
    <span class="domysubs-badge">פלט SRT</span>
  </div>
</div>
"""

FOOTER_HTML = """
<div class="domysubs-footer">
  מבוסס על <a href="https://github.com/m-bain/whisperX" target="_blank">WhisperX</a>
  · דורש ffmpeg · yt-dlp ליוטיוב · פלט ב-<code>workspace/output/</code>
</div>
"""
