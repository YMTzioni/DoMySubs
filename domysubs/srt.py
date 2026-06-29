from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str


SINGLE_TS_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})"
)


def timestamp_to_seconds(ts: str) -> float:
    match = SINGLE_TS_RE.match(ts.strip())
    if not match:
        raise ValueError(f"Invalid timestamp: {ts}")
    g = match.groupdict()
    return (
        int(g["h"]) * 3600
        + int(g["m"]) * 60
        + int(g["s"])
        + int(g["ms"]) / 1000
    )


def seconds_to_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_srt(content: str) -> list[SubtitleCue]:
    content = content.replace("\r\n", "\n").strip()
    if not content:
        return []

    blocks = re.split(r"\n\s*\n", content)
    cues: list[SubtitleCue] = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        try:
            index = int(lines[0])
        except ValueError:
            index = len(cues) + 1
            time_line = lines[0]
            text_lines = lines[1:]
        else:
            time_line = lines[1]
            text_lines = lines[2:]

        if "-->" not in time_line:
            continue

        start_str, end_str = [part.strip() for part in time_line.split("-->")]
        text = "\n".join(text_lines).strip()
        cues.append(
            SubtitleCue(
                index=index,
                start=timestamp_to_seconds(start_str),
                end=timestamp_to_seconds(end_str),
                text=text,
            )
        )

    return cues


def read_srt(path: str) -> list[SubtitleCue]:
    with open(path, encoding="utf-8-sig") as f:
        return parse_srt(f.read())


def write_srt(cues: list[SubtitleCue]) -> str:
    parts: list[str] = []
    for i, cue in enumerate(cues, start=1):
        parts.append(str(i))
        parts.append(
            f"{seconds_to_timestamp(cue.start)} --> {seconds_to_timestamp(cue.end)}"
        )
        parts.append(cue.text)
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def save_srt(cues: list[SubtitleCue], path: str) -> str:
    content = write_srt(cues)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
