#!/usr/bin/env python3
# captr/burn.py

"""
ffmpeg / libass burn-in.

Renders an .ass subtitle file onto a video with ffmpeg's libass-backed 'ass'
filter, copying the original audio through untouched.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Tuple


logger = logging.getLogger(__name__)


def video_dimensions(video: str) -> Tuple[int, int]:
    """Return (width, height) of the first video stream via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", video,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {video}: {proc.stderr[-400:]}")
    streams = json.loads(proc.stdout).get("streams", [])
    if not streams:
        raise RuntimeError(f"No video stream found in {video}.")
    return int(streams[0]["width"]), int(streams[0]["height"])


def _escape_filter_path(path: str) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    # In filtergraphs, ':' and '\' are special and "'" delimits.
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def burn(video: str, ass_path: str, out_path: str, *, crf: int = 18) -> str:
    """
    Burn ``ass_path`` onto ``video`` and write ``out_path``.

    Video is re-encoded (libx264) because subtitles are rasterised into frames;
    audio is stream-copied. Returns out_path.

    Raises:
        RuntimeError: if ffmpeg exits non-zero.
    """
    if not Path(video).is_file():
        raise FileNotFoundError(f"Video not found: {video}")
    if not Path(ass_path).is_file():
        raise FileNotFoundError(f"ASS file not found: {ass_path}")

    vf = f"ass='{_escape_filter_path(ass_path)}'"
    cmd = [
        "ffmpeg", "-y", "-i", video,
        "-vf", vf,
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-c:a", "copy",
        out_path,
    ]
    logger.info("Burning subtitles: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg burn failed (exit {proc.returncode}).\n"
            f"stderr: {proc.stderr[-800:]}"
        )
    return out_path
