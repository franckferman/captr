#!/usr/bin/env python3
# captr/cli.py

"""
captr - burn styled subtitles onto a video.

captr transcribes with whispr, renders the transcript to an ASS subtitle file
using a chosen style preset, and burns it onto the video with ffmpeg/libass.

    captr video.mp4 --style film --lang en -o subtitled.mp4
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

from captr.ass import build_ass
from captr.burn import burn, video_dimensions
from captr.styles import DEFAULT_STYLE, STYLES, get_style
from captr.transcribe import default_whispr_dir, transcribe


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="captr",
        description="Burn styled subtitles onto a video (whispr + libass).",
    )
    p.add_argument("video", help="input video file")
    p.add_argument("--style", "-s", default=DEFAULT_STYLE,
                   choices=sorted(STYLES), help=f"subtitle style (default: {DEFAULT_STYLE})")
    p.add_argument("--lang", "-l", default=None,
                   help="ISO 639-1 language code (auto-detect if omitted)")
    p.add_argument("--backend", "-b", default="faster_whisper",
                   help="whispr backend (default: faster_whisper)")
    p.add_argument("--translate-to", default=None,
                   help="translate subtitles to this ISO 639-1 code (whispr)")
    p.add_argument("--output", "-o", default=None,
                   help="output video path (default: <input>.captr.mp4)")
    p.add_argument("--whispr", default=default_whispr_dir(),
                   help="path to a whispr clone (or set $WHISPR_DIR)")
    p.add_argument("--ass-only", action="store_true",
                   help="write the .ass file only; do not burn the video")
    p.add_argument("--keep-ass", action="store_true",
                   help="keep the generated .ass next to the output")
    p.add_argument("--debug", action="store_true", help="verbose logging")
    return p


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("captr")

    video = args.video
    if not Path(video).is_file():
        print(f"[ERROR] Video not found: {video}", file=sys.stderr)
        return 2

    try:
        style = get_style(args.style)

        log.info("Transcribing with whispr (%s)...", args.backend)
        result = transcribe(
            video, whispr_dir=args.whispr,
            backend=args.backend, language=args.lang,
            translate_to=args.translate_to,
        )
        segments = result.get("segments", [])
        if not segments:
            print("[ERROR] whispr returned no segments.", file=sys.stderr)
            return 1
        log.info("Got %d segment(s) in '%s'.", len(segments), result.get("language"))

        width, height = video_dimensions(video)
        ass_doc = build_ass(segments, style, width, height,
                            title=Path(video).stem)

        out = args.output or f"{Path(video).with_suffix('')}.captr.mp4"
        ass_out = Path(out).with_suffix(".ass")

        if args.ass_only or args.keep_ass:
            ass_out.write_text(ass_doc, encoding="utf-8")
            log.info("Wrote ASS: %s", ass_out)
            if args.ass_only:
                return 0
            ass_path = str(ass_out)
            burn(video, ass_path, out)
        else:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".ass", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(ass_doc)
                ass_path = fh.name
            try:
                burn(video, ass_path, out)
            finally:
                os.unlink(ass_path)

        log.info("Done: %s", out)
        print(out)
        return 0

    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
