"""CLI לשימוש משורת הפקודה."""

from __future__ import annotations

import argparse
import logging
import sys

from domysubs.batch import format_batch_summary, process_folder
from domysubs.config import Settings, get_settings
from domysubs.pipeline import process_input, process_srt

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _ensure_utf8_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DoMySubs - הפקת כתוביות בעברית מוידאו, אודיו, יוטיוב או SRT",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="נתיב לקובץ (וידאו/אודיו/SRT) או קישור יוטיוב",
    )
    parser.add_argument(
        "-l", "--language",
        default=None,
        help="שפת מקור (ברירת מחדל: זיהוי אוטומטי)",
    )
    parser.add_argument(
        "--device",
        default=None,
        choices=["cpu", "cuda"],
        help="מכשיר חישוב",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="מודל Whisper (tiny/base/small/medium/large-v2/large-v3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="גודל batch לתמלול",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="ללא תרגום - שמור בשפת המקור",
    )
    parser.add_argument(
        "--srt-only",
        action="store_true",
        help="תרגם SRT קיים בלבד (ללא תמלול)",
    )
    parser.add_argument(
        "--scan-hardware",
        action="store_true",
        help="סרוק חומרה והצג הגדרות מומלצות",
    )
    parser.add_argument(
        "--batch-folder",
        default=None,
        help="עיבוד אצווה: נתיב לתיקייה עם סרטונים",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="תיקיית פלט (לאצווה או קובץ בודד)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="אצווה: אל תסרוק תת-תיקיות",
    )

    args = parser.parse_args(argv)

    if args.scan_hardware:
        from domysubs.hardware import format_scan_report, recommend_settings, scan_hardware

        _ensure_utf8_stdout()
        rec = recommend_settings(scan_hardware())
        print(format_scan_report(rec))
        print(f"\nלהחלה: --device {rec.settings.device} --model {rec.settings.model} "
              f"--batch-size {rec.settings.batch_size}")
        return 0

    if not args.input and not args.batch_folder:
        parser.error("נדרש קלט (קובץ/קישור), --batch-folder, או --scan-hardware")

    base = get_settings()

    settings = Settings(
        device=args.device or base.device,
        model=args.model or base.model,
        batch_size=args.batch_size or base.batch_size,
        compute_type=base.compute_type,
        hf_token=base.hf_token,
    )

    def on_progress(msg: str, pct: float):
        print(f"[{int(pct):3d}%] {msg}", flush=True)

    try:
        if args.batch_folder:
            _ensure_utf8_stdout()
            result = process_folder(
                args.batch_folder,
                output_dir=args.output,
                recursive=not args.no_recursive,
                settings=settings,
                source_language=args.language,
                skip_translation=args.no_translate,
                progress=on_progress,
            )
            print("\n" + format_batch_summary(result))
            return 0 if result.failed == 0 else 1

        if args.srt_only or args.input.lower().endswith(".srt"):
            out_path, cues = process_srt(
                args.input,
                source_language=args.language or "auto",
                progress=on_progress,
            )
            print(f"\nנשמר: {out_path} ({len(cues)} שורות)")
        else:
            out_path, cues, lang = process_input(
                args.input,
                settings=settings,
                source_language=args.language,
                skip_translation=args.no_translate,
                progress=on_progress,
            )
            if args.output and not args.input.lower().endswith(".srt"):
                from pathlib import Path
                from domysubs.srt import save_srt
                dest = Path(args.output)
                if dest.is_dir():
                    dest = dest / (Path(args.input).stem + ".srt")
                dest.parent.mkdir(parents=True, exist_ok=True)
                save_srt(cues, str(dest))
                out_path = str(dest)
            print(f"\nנשמר: {out_path} ({len(cues)} שורות, שפת מקור: {lang})")
        return 0
    except Exception as exc:
        logger.error("שגיאה: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
