from __future__ import annotations

import csv
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from domysubs.audio import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
from domysubs.config import WORK_DIR, Settings, get_settings
from domysubs.pipeline import ProgressCallback, process_media

logger = logging.getLogger(__name__)

MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


@dataclass
class BatchItemResult:
    video_name: str
    video_path: str
    srt_name: str
    srt_path: str
    status: str
    source_language: str = ""
    cue_count: int = 0
    error: str = ""


@dataclass
class BatchResult:
    output_dir: str
    items: list[BatchItemResult] = field(default_factory=list)
    manifest_path: str = ""
    zip_path: str = ""

    @property
    def succeeded(self) -> int:
        return sum(1 for i in self.items if i.status == "הצליח")

    @property
    def failed(self) -> int:
        return sum(1 for i in self.items if i.status != "הצליח")


def discover_media_files(folder: str | Path, recursive: bool = True) -> list[Path]:
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"תיקייה לא קיימת: {root}")

    if recursive:
        candidates = root.rglob("*")
    else:
        candidates = root.glob("*")

    files = [
        p for p in candidates
        if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS
    ]
    return sorted(files, key=lambda p: p.name.lower())


def _default_batch_output_dir(source_folder: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return source_folder / "DoMySubs_output" / ts


def export_manifest_excel(items: list[BatchItemResult], path: Path) -> Path:
    """ייצוא מניפסט ל-Excel (או CSV אם openpyxl לא מותקן)."""
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "שם וידאו",
        "שם קובץ SRT",
        "מיקום SRT",
        "מיקום וידאו",
        "סטטוס",
        "שפת מקור",
        "מספר שורות",
    ]
    rows = [
        [
            item.video_name,
            item.srt_name,
            item.srt_path,
            item.video_path,
            item.status,
            item.source_language,
            item.cue_count,
        ]
        for item in items
    ]

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = "כתוביות"
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append(row)
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 55
        ws.column_dimensions["D"].width = 55
        wb.save(path)
    except ImportError:
        csv_path = path.with_suffix(".csv")
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return csv_path

    return path


def create_batch_zip(output_dir: Path, items: list[BatchItemResult]) -> Path | None:
    """אורז את כל קבצי ה-SRT + המניפסט ל-ZIP."""
    srt_files = [Path(i.srt_path) for i in items if i.status == "הצליח" and Path(i.srt_path).exists()]
    if not srt_files:
        return None

    zip_path = output_dir / "כתוביות_מאוגדות.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for srt in srt_files:
            zf.write(srt, arcname=srt.name)
        manifest = output_dir / "manifest.xlsx"
        if manifest.exists():
            zf.write(manifest, arcname=manifest.name)
        manifest_csv = output_dir / "manifest.csv"
        if manifest_csv.exists():
            zf.write(manifest_csv, arcname=manifest_csv.name)
    return zip_path


def process_folder(
    folder: str | Path,
    output_dir: str | Path | None = None,
    *,
    recursive: bool = True,
    settings: Settings | None = None,
    source_language: str | None = None,
    skip_translation: bool = False,
    progress: ProgressCallback | None = None,
) -> BatchResult:
    """
    עיבוד אצווה של כל הסרטונים בתיקייה.
    כל SRT נשמר באותו שם כמו קובץ המקור.
    """
    settings = settings or get_settings()
    source = Path(folder).expanduser().resolve()
    out = Path(output_dir).expanduser().resolve() if output_dir else _default_batch_output_dir(source)
    out.mkdir(parents=True, exist_ok=True)

    media_files = discover_media_files(source, recursive=recursive)
    if not media_files:
        raise ValueError(f"לא נמצאו קבצי וידאו/אודיו בתיקייה: {source}")

    total = len(media_files)
    results: list[BatchItemResult] = []

    for index, media_path in enumerate(media_files, start=1):
        srt_path = out / f"{media_path.stem}.srt"
        base_pct = ((index - 1) / total) * 100

        def file_progress(msg: str, pct: float, _base=base_pct, _idx=index, _total=total):
            if progress:
                overall = _base + (pct / 100) * (100 / _total)
                progress(f"[{_idx}/{_total}] {media_path.name}: {msg}", overall)

        item = BatchItemResult(
            video_name=media_path.name,
            video_path=str(media_path),
            srt_name=srt_path.name,
            srt_path=str(srt_path),
            status="מעבד",
        )

        try:
            if progress:
                progress(f"[{index}/{total}] מתחיל: {media_path.name}", base_pct)

            _, cues, lang = process_media(
                str(media_path),
                settings=settings,
                source_language=source_language,
                skip_translation=skip_translation,
                progress=file_progress,
                output_path=srt_path,
            )
            item.status = "הצליח"
            item.source_language = lang or ""
            item.cue_count = len(cues)
        except Exception as exc:
            logger.exception("Batch item failed: %s", media_path)
            item.status = "נכשל"
            item.error = str(exc)

        results.append(item)

    manifest = export_manifest_excel(results, out / "manifest.xlsx")
    zip_path = create_batch_zip(out, results)

    if progress:
        progress(
            f"הושלם: {sum(1 for r in results if r.status == 'הצליח')}/{total} קבצים",
            100,
        )

    return BatchResult(
        output_dir=str(out),
        items=results,
        manifest_path=str(manifest),
        zip_path=str(zip_path) if zip_path else "",
    )


def format_batch_summary(result: BatchResult) -> str:
    lines = [
        f"תיקיית פלט: {result.output_dir}",
        f"הצליחו: {result.succeeded} | נכשלו: {result.failed} | סה\"כ: {len(result.items)}",
        f"מניפסט: {result.manifest_path}",
    ]
    if result.zip_path:
        lines.append(f"ZIP: {result.zip_path}")
    lines.append("")
    for item in result.items:
        mark = "✓" if item.status == "הצליח" else "✗"
        lines.append(f"{mark} {item.video_name} → {item.srt_name} ({item.status})")
        if item.error:
            lines.append(f"    שגיאה: {item.error}")
    return "\n".join(lines)
