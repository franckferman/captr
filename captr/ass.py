#!/usr/bin/env python3
# captr/ass.py

"""
ASS Subtitle Generation

Description:
Builds Advanced SubStation Alpha (.ass) documents from transcript segments.
ASS is what libass (and thus ffmpeg) renders, and it is the format that lets a
style preset control font, colour, position, outline and -- later -- per-word
karaoke/animation.

A StyleSpec describes one preset's [V4+ Styles] line. build_ass() lays out the
[Script Info]/[V4+ Styles]/[Events] sections and emits one Dialogue per segment.

Created By  : Franck FERMAN
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class StyleSpec:
    """One subtitle style preset -> an ASS 'Style:' definition.

    Colours are ASS format: &HAABBGGRR (alpha, blue, green, red); AA=00 opaque.
    Alignment uses the numpad convention (2 = bottom-centre, 5 = middle-centre,
    8 = top-centre).
    """
    name: str
    fontname: str = "Arial"
    fontsize: int = 48
    primary_colour: str = "&H00FFFFFF"   # white text
    outline_colour: str = "&H00000000"   # black outline
    back_colour: str = "&H64000000"      # semi-transparent shadow box
    bold: int = 0                        # -1 = bold, 0 = normal
    italic: int = 0
    outline: float = 2.0
    shadow: float = 0.0
    alignment: int = 2
    margin_l: int = 40
    margin_r: int = 40
    margin_v: int = 40

    def to_style_line(self) -> str:
        """Render the ASS 'Style:' line for the [V4+ Styles] section."""
        fields = [
            self.name, self.fontname, self.fontsize,
            self.primary_colour, "&H000000FF", self.outline_colour, self.back_colour,
            self.bold, self.italic, 0, 0,          # Bold, Italic, Underline, StrikeOut
            100, 100, 0, 0,                        # ScaleX, ScaleY, Spacing, Angle
            1,                                     # BorderStyle: 1 = outline+shadow
            self.outline, self.shadow,
            self.alignment,
            self.margin_l, self.margin_r, self.margin_v,
            1,                                     # Encoding
        ]
        return "Style: " + ",".join(str(f) for f in fields)


_STYLE_FORMAT = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
    "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
    "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
    "MarginR, MarginV, Encoding"
)
_EVENT_FORMAT = (
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
    "Effect, Text"
)


def ass_timestamp(seconds: float) -> str:
    """Format seconds as an ASS timestamp: H:MM:SS.cc (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    total_cs = int(round(seconds * 100))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape_text(text: str) -> str:
    """Escape text for an ASS Dialogue line (newlines -> \\N, braces neutralised)."""
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", "\\N")
        .strip()
    )


def build_ass(
    segments: List[dict],
    style: StyleSpec,
    width: int,
    height: int,
    title: Optional[str] = None,
) -> str:
    """
    Build a complete ASS document from segment dicts.

    Each segment needs 'start', 'end' and 'text'. One Dialogue line is emitted
    per non-empty segment, using the given style.

    Args:
        segments: List of {'start', 'end', 'text'} (word data, if any, ignored
                  by this segment-level layout).
        style:    The StyleSpec preset to render with.
        width:    Video width  -> PlayResX (so positions map 1:1 to the frame).
        height:   Video height -> PlayResY.
        title:    Optional script title.

    Returns:
        The ASS document as a string.
    """
    lines: List[str] = []
    lines.append("[Script Info]")
    if title:
        lines.append(f"Title: {title}")
    lines.append("ScriptType: v4.00+")
    lines.append("WrapStyle: 2")
    lines.append("ScaledBorderAndShadow: yes")
    lines.append(f"PlayResX: {width}")
    lines.append(f"PlayResY: {height}")
    lines.append("")
    lines.append("[V4+ Styles]")
    lines.append(_STYLE_FORMAT)
    lines.append(style.to_style_line())
    lines.append("")
    lines.append("[Events]")
    lines.append(_EVENT_FORMAT)

    for seg in segments:
        text = escape_text(str(seg.get("text", "")))
        if not text:
            continue
        start = ass_timestamp(float(seg.get("start", 0.0)))
        end = ass_timestamp(float(seg.get("end", 0.0)))
        lines.append(
            f"Dialogue: 0,{start},{end},{style.name},,0,0,0,,{text}"
        )

    return "\n".join(lines) + "\n"
