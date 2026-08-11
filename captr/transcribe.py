#!/usr/bin/env python3
# captr/transcribe.py

"""
whispr integration.

captr does not re-implement ASR. It drives whispr (the sibling project) as a
subprocess to produce a JSON transcript -- optionally with per-word timestamps
and/or a translation -- and returns the parsed result for styling.

whispr is not on PyPI, so its location is given explicitly (``whispr_dir``,
default $WHISPR_DIR or ~/maldev/whispr).
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def default_whispr_dir() -> str:
    """Best-effort default location of the whispr project."""
    return os.environ.get("WHISPR_DIR") or str(Path.home() / "maldev" / "whispr")


def build_command(
    video: str,
    out_json_dir: str,
    whispr_dir: str,
    *,
    backend: str = "faster_whisper",
    language: Optional[str] = None,
    word_timestamps: bool = False,
    word_timestamps_provider: Optional[str] = None,
    translate_to: Optional[str] = None,
    python_bin: str = sys.executable,
    prefix: str = "captr",
) -> list:
    """Construct the whispr CLI command (returned as an argv list)."""
    main_py = str(Path(whispr_dir) / "main.py")
    cmd = [
        python_bin, main_py,
        "--file", video,
        "--backend", backend,
        "--format", "json",
        "--output-dir", out_json_dir,
        "--output-prefix", prefix,
    ]
    if language:
        cmd += ["--language", language]
    if word_timestamps:
        cmd += ["--word-timestamps"]
        if word_timestamps_provider:
            cmd += ["--word-timestamps-provider", word_timestamps_provider]
    if translate_to:
        cmd += ["--translate-to", translate_to]
    return cmd


def transcribe(
    video: str,
    whispr_dir: Optional[str] = None,
    *,
    backend: str = "faster_whisper",
    language: Optional[str] = None,
    word_timestamps: bool = False,
    word_timestamps_provider: Optional[str] = None,
    translate_to: Optional[str] = None,
    python_bin: str = sys.executable,
    timeout: int = 3600,
) -> dict:
    """
    Transcribe ``video`` via whispr and return the parsed JSON result.

    When ``translate_to`` is set, the translated JSON ('{prefix}.{lang}.json')
    is returned so the styled subtitles are in the target language.

    Raises:
        FileNotFoundError: whispr's main.py or its JSON output is missing.
        RuntimeError:      whispr exited non-zero.
    """
    whispr_dir = whispr_dir or default_whispr_dir()
    main_py = Path(whispr_dir) / "main.py"
    if not main_py.is_file():
        raise FileNotFoundError(
            f"whispr not found at {main_py}. Point --whispr at a whispr clone "
            f"or set $WHISPR_DIR."
        )
    if not Path(video).is_file():
        raise FileNotFoundError(f"Video not found: {video}")

    with tempfile.TemporaryDirectory(prefix="captr_asr_") as d:
        prefix = "captr"
        cmd = build_command(
            video, d, whispr_dir,
            backend=backend, language=language,
            word_timestamps=word_timestamps,
            word_timestamps_provider=word_timestamps_provider,
            translate_to=translate_to, python_bin=python_bin, prefix=prefix,
        )
        logger.info("Running whispr: %s", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(
                f"whispr failed (exit {proc.returncode}).\n"
                f"stderr: {proc.stderr[-800:]}"
            )

        # When translating, prefer the translated JSON.
        name = f"{prefix}.{translate_to}.json" if translate_to else f"{prefix}.json"
        json_path = Path(d) / name
        if not json_path.is_file():
            raise FileNotFoundError(
                f"Expected whispr output {json_path} was not produced."
            )
        with json_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
