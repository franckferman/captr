#!/usr/bin/env python3
# captr/cli.py

"""
captr - burn (or mux) styled subtitles onto a video.

captr transcribes with whispr, renders the transcript to an ASS subtitle file
using a chosen style preset, and either burns it onto the video (libass) or
muxes it as a soft, toggleable track.

    captr video.mp4 --style film --lang en -o subtitled.mp4
    captr video.mp4 --style pop  --lang en -o captions.mp4     # word-animated
    captr video.mp4 --style film --soft   -o soft.mkv          # toggleable track
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

from captr.ass import build_ass
from captr.burn import burn, mux_soft, video_dimensions
from captr.styles import DEFAULT_STYLE, STYLES, get_style
from captr.transcribe import default_whispr_dir, transcribe


def build_parser() -> argparse.ArgumentParser:
    """Build the captr command-line parser."""
    p = argparse.ArgumentParser(
        prog="captr",
        description="Burn or mux styled subtitles onto a video (whispr + libass).",
        epilog=(
            "examples:\n"
            "  captr talk.mp4 --style film --lang en\n"
            "  captr talk.mp4 --style pop --lang en          # word-animated\n"
            "  captr talk.mp4 --style film --soft            # toggleable track\n"
            "  captr talk.mp4 --style translation --translate-to en\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("video", metavar="VIDEO", help="input video file")

    style = p.add_argument_group("style")
    style.add_argument("--style", "-s", default=DEFAULT_STYLE, choices=sorted(STYLES),
                       help=f"subtitle style (default: {DEFAULT_STYLE})")

    asr = p.add_argument_group("transcription (whispr)")
    asr.add_argument("--lang", "-l", default=None,
                     help="ISO 639-1 language code (auto-detected if omitted)")
    asr.add_argument("--backend", "-b", default="faster_whisper",
                     help="whispr ASR backend (default: faster_whisper)")
    asr.add_argument("--translate-to", default=None, metavar="LANG",
                     help="translate subtitles into this ISO 639-1 code (local, via whispr)")
    asr.add_argument("--word-provider", default=None,
                     choices=["native", "stable_ts", "whisperx"],
                     help="word-timestamp source for animated styles (whispr default: native)")
    asr.add_argument("--whispr", default=None,
                     help="path to a whispr clone (default: $WHISPR_DIR, else a sibling ./whispr)")

    out = p.add_argument_group("output")
    out.add_argument("--soft", action="store_true",
                     help="mux subtitles as a soft/toggleable track (.mkv) instead of burning")
    out.add_argument("--output", "-o", default=None,
                     help="output path (default: <input>.captr.mp4, or .mkv with --soft)")
    out.add_argument("--ass-only", action="store_true",
                     help="write the .ass subtitle file only; do not burn or mux")
    out.add_argument("--keep-ass", action="store_true",
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

    # Resolve whispr here (kept out of --help so it never prints a machine path).
    args.whispr = args.whispr or default_whispr_dir()

    video = args.video
    if not Path(video).is_file():
        print(f"[ERROR] Video not found: {video}", file=sys.stderr)
        return 2

    try:
        style = get_style(args.style)

        log.info("Transcribing with whispr (%s)%s...", args.backend,
                 " + word timings" if style.word_level else "")
        result = transcribe(
            video, whispr_dir=args.whispr,
            backend=args.backend, language=args.lang,
            word_timestamps=style.word_level,
            word_timestamps_provider=args.word_provider,
            translate_to=args.translate_to,
        )
        segments = result.get("segments", [])
        if not segments:
            print("[ERROR] whispr returned no segments.", file=sys.stderr)
            return 1
        log.info("Got %d segment(s) in '%s'.", len(segments), result.get("language"))
        if style.word_level and not any(s.get("words") for s in segments):
            log.warning(
                "Style '%s' is word-animated but whispr returned no word timings; "
                "falling back to segment-level lines.", args.style,
            )

        width, height = video_dimensions(video)
        ass_doc = build_ass(segments, style, width, height,
                            title=Path(video).stem, word_level=style.word_level)

        # Default container: .mkv for soft subs (keeps ASS styling), else .mp4.
        default_ext = ".captr.mkv" if args.soft else ".captr.mp4"
        out = args.output or f"{Path(video).with_suffix('')}{default_ext}"
        ass_out = Path(out).with_suffix(".ass")

        write_ass_beside = args.ass_only or args.keep_ass
        if write_ass_beside:
            ass_out.write_text(ass_doc, encoding="utf-8")
            log.info("Wrote ASS: %s", ass_out)
            if args.ass_only:
                return 0
            ass_path = str(ass_out)
            _render(args.soft, video, ass_path, out)
        else:
            # delete=False: close the handle so ffmpeg can reopen it by path;
            # removed in the finally below.
            with tempfile.NamedTemporaryFile(
                "w", suffix=".ass", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(ass_doc)
                ass_path = fh.name
            try:
                _render(args.soft, video, ass_path, out)
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


def _render(soft: bool, video: str, ass_path: str, out: str) -> None:
    """Burn or soft-mux the ASS onto the video."""
    if soft:
        mux_soft(video, ass_path, out)
    else:
        burn(video, ass_path, out)


if __name__ == "__main__":
    sys.exit(main())
