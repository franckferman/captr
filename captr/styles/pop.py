#!/usr/bin/env python3
# captr/styles/pop.py

"""
'pop' preset — animated word-by-word captions (TikTok / Reels look).

Big, bold, centred. Each word highlights on its own timing (ASS karaoke), so the
line fills word-by-word in sync with the speech. Requires per-word timestamps,
which captr requests from whispr automatically for this style.

Primary is the 'spoken' colour (bright yellow), secondary the upcoming colour
(white); a thick black outline keeps it legible over any footage.
"""

from captr.ass import StyleSpec

POP = StyleSpec(
    name="Pop",
    fontname="DejaVu Sans",
    fontsize=64,
    primary_colour="&H0000F0FF",   # bright yellow (BBGGRR) -> spoken word
    secondary_colour="&H00FFFFFF",  # white -> upcoming word
    outline_colour="&H00000000",
    back_colour="&H50000000",
    bold=-1,                        # bold
    outline=3.0,
    shadow=1.0,
    alignment=2,                    # bottom-centre
    margin_v=90,
    word_level=True,
)
