from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

from domysubs.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class GpuInfo:
    available: bool = False
    name: str = ""
    vram_gb: float = 0.0
    cuda_version: str | None = None
    device_count: int = 0


@dataclass
class HardwareProfile:
    os_name: str = ""
    cpu_name: str = ""
    cpu_cores: int = 0
    ram_gb: float = 0.0
    gpu: GpuInfo = field(default_factory=GpuInfo)
    ffmpeg_available: bool = False
    ytdlp_available: bool = False
    python_version: str = ""


@dataclass
class HardwareRecommendation:
    settings: Settings
    profile: HardwareProfile
    tier: str
    summary: str
    details: list[str]


def _get_ram_gb() -> float:
    try:
        if sys.platform == "win32":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullTotalPhys / (1024**3), 1)
        if sys.platform == "darwin":
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0:
                return round(int(out.stdout.strip()) / (1024**3), 1)
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return round(kb / (1024**2), 1)
    except Exception as exc:
        logger.debug("RAM detection failed: %s", exc)
    return 0.0


def _get_cpu_name() -> str:
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["wmic", "cpu", "get", "name"],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            lines = [ln.strip() for ln in out.stdout.splitlines() if ln.strip() and ln.strip() != "Name"]
            if lines:
                return lines[0]
        elif sys.platform == "darwin":
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0:
                return out.stdout.strip()
        else:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception as exc:
        logger.debug("CPU name detection failed: %s", exc)
    return platform.processor() or "לא זוהה"


def _get_gpu_info() -> GpuInfo:
    info = GpuInfo()
    try:
        import torch

        info.cuda_version = torch.version.cuda
        info.device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        info.available = info.device_count > 0

        if info.available:
            props = torch.cuda.get_device_properties(0)
            info.name = torch.cuda.get_device_name(0)
            info.vram_gb = round(props.total_memory / (1024**3), 1)
    except Exception as exc:
        logger.debug("GPU detection failed: %s", exc)
    return info


def scan_hardware() -> HardwareProfile:
    return HardwareProfile(
        os_name=f"{platform.system()} {platform.release()} ({platform.machine()})",
        cpu_name=_get_cpu_name(),
        cpu_cores=os.cpu_count() or 1,
        ram_gb=_get_ram_gb(),
        gpu=_get_gpu_info(),
        ffmpeg_available=shutil.which("ffmpeg") is not None,
        ytdlp_available=shutil.which("yt-dlp") is not None,
        python_version=platform.python_version(),
    )


def recommend_settings(profile: HardwareProfile | None = None) -> HardwareRecommendation:
    profile = profile or scan_hardware()
    details: list[str] = []

    if profile.gpu.available:
        vram = profile.gpu.vram_gb
        device = "cuda"
        compute_type = "float16"

        if vram >= 12:
            model = "large-v2"
            batch_size = 16
            tier = "גבוה (GPU חזק)"
            details.append(f"זיכרון GPU של {vram}GB מאפשר מודל large-v2 עם batch גבוה.")
        elif vram >= 8:
            model = "large-v2"
            batch_size = 8
            tier = "טוב (GPU בינוני-חזק)"
            details.append(f"זיכרון GPU של {vram}GB מתאים ל-large-v2 עם batch בינוני.")
        elif vram >= 6:
            model = "medium"
            batch_size = 8
            tier = "בינוני (GPU עם מעט VRAM)"
            details.append(f"זיכרון GPU של {vram}GB — medium יציב יותר מ-large על המכונה הזו.")
        elif vram >= 4:
            model = "small"
            batch_size = 4
            compute_type = "int8"
            tier = "מוגבל (GPU חלש)"
            details.append(f"זיכרון GPU של {vram}GB — small + int8 למניעת קריסות זיכרון.")
        else:
            model = "base"
            batch_size = 2
            compute_type = "int8"
            tier = "מינימלי (GPU עם VRAM נמוך)"
            details.append(f"זיכרון GPU של {vram}GB — הגדרות שמרניות מאוד.")
    else:
        device = "cpu"
        compute_type = "int8"
        ram = profile.ram_gb
        cores = profile.cpu_cores

        if ram >= 32 and cores >= 8:
            model = "medium"
            batch_size = 4
            tier = "CPU חזק"
            details.append(f"{ram}GB RAM ו-{cores} ליבות — medium אפשרי, אך עדיין איטי יחסית ל-GPU.")
        elif ram >= 16 and cores >= 4:
            model = "small"
            batch_size = 4
            tier = "CPU בינוני"
            details.append(f"{ram}GB RAM — small הוא איזון טוב בין דיוק למהירות על CPU.")
        elif ram >= 8:
            model = "small"
            batch_size = 2
            tier = "CPU בסיסי"
            details.append(f"{ram}GB RAM — small עם batch נמוך למניעת תקיעות.")
        else:
            model = "base"
            batch_size = 1
            tier = "CPU מוגבל"
            details.append(f"{ram}GB RAM — base מומלץ למניעת חוסר זיכרון.")

        details.append("לא זוהה GPU עם CUDA — העיבוד יתבצע על המעבד.")

    if not profile.ffmpeg_available:
        details.append("ffmpeg לא נמצא ב-PATH — נדרש לעיבוד וידאו.")
    if not profile.ytdlp_available:
        details.append("yt-dlp לא נמצא ב-PATH — נדרש להורדות מיוטיוב.")

    settings = Settings(
        device=device,
        model=model,
        batch_size=batch_size,
        compute_type=compute_type,
    )

    gpu_line = (
        f"{profile.gpu.name} ({profile.gpu.vram_gb}GB VRAM)"
        if profile.gpu.available
        else "לא זמין"
    )

    summary = (
        f"דרגה: {tier}\n"
        f"מומלץ: {device} | {model} | batch={batch_size} | {compute_type}"
    )

    return HardwareRecommendation(
        settings=settings,
        profile=profile,
        tier=tier,
        summary=summary,
        details=details,
    )


def format_scan_report(rec: HardwareRecommendation) -> str:
    p = rec.profile
    g = p.gpu
    lines = [
        "## דוח חומרה",
        "",
        f"**מערכת:** {p.os_name}",
        f"**מעבד:** {p.cpu_name} ({p.cpu_cores} ליבות)",
        f"**זיכרון RAM:** {p.ram_gb} GB",
        f"**GPU:** {g.name or 'לא זוהה'}",
    ]

    if g.available:
        lines.append(f"**VRAM:** {g.vram_gb} GB")
        lines.append(f"**CUDA:** {g.cuda_version or 'לא ידוע'}")
    else:
        lines.append("**CUDA:** לא זמין")

    lines.extend([
        "",
        f"**ffmpeg:** {'זמין' if p.ffmpeg_available else 'חסר'}",
        f"**yt-dlp:** {'זמין' if p.ytdlp_available else 'חסר'}",
        f"**Python:** {p.python_version}",
        "",
        "## המלצה",
        "",
        rec.summary,
        "",
    ])

    if rec.details:
        lines.append("### הסבר")
        for item in rec.details:
            lines.append(f"- {item}")

    return "\n".join(lines)
