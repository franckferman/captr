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
    primary_colour: str = "&H00FFFFFF"   # text colour (and karaoke 'sung' colour)
    secondary_colour: str = "&H000000FF"  # karaoke upcoming-word colour
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
    # True if this preset renders per-word (karaoke) and thus needs word timings.
    word_level: bool = False

    def to_style_line(self) -> str:
        """Render the ASS 'Style:' line for the [V4+ Styles] section."""
        fields = [
            self.name, self.fontname, self.fontsize,
            self.primary_colour, self.secondary_colour, self.outline_colour, self.back_colour,
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


def _karaoke_text(words: List[dict]) -> str:
    """
    Build an ASS karaoke line from word dicts: '{\\kN}word ' per word.

    Each word stays in the style's secondary colour until its turn, then flips
    to the primary colour -- libass animates this word-by-word, in sync with the
    per-word timings from whispr.
    """
    parts: List[str] = []
    for w in words:
        dur_cs = max(1, int(round((float(w["end"]) - float(w["start"])) * 100)))
        token = escape_text(str(w.get("word", "")))
        if not token:
            continue
        parts.append("{\\k%d}%s" % (dur_cs, token))
    return " ".join(parts)


def build_ass(
    segments: List[dict],
    style: StyleSpec,
    width: int,
    height: int,
    title: Optional[str] = None,
    word_level: bool = False,
) -> str:
    """
    Build a complete ASS document from segment dicts.

    With ``word_level`` False (default), one Dialogue is emitted per segment
    (film / translation styles). With ``word_level`` True, segments that carry a
    'words' list are rendered as karaoke lines that highlight each word on its
    own timing (the 'pop' style); segments without words fall back to plain.

    Args:
        segments: List of {'start', 'end', 'text'[, 'words']}.
        style:    The StyleSpec preset to render with.
        width:    Video width  -> PlayResX (positions map 1:1 to the frame).
        height:   Video height -> PlayResY.
        title:    Optional script title.
        word_level: Emit per-word karaoke when word data is present.

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
        words = seg.get("words") if word_level else None
        if words:
            # Align the cue to the words themselves for tight highlighting.
            start = ass_timestamp(float(words[0]["start"]))
            end = ass_timestamp(float(words[-1]["end"]))
            text = _karaoke_text(words)
        else:
            text = escape_text(str(seg.get("text", "")))
            start = ass_timestamp(float(seg.get("start", 0.0)))
            end = ass_timestamp(float(seg.get("end", 0.0)))
        if not text:
            continue
        lines.append(
            f"Dialogue: 0,{start},{end},{style.name},,0,0,0,,{text}"
        )

    return "\n".join(lines) + "\n"
