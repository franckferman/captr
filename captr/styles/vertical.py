#!/usr/bin/env python3
# captr/styles/vertical.py

"""
Vertical (9:16) presets for phone / Shorts / Reels footage.

Same looks as the horizontal presets, but the vertical safe area is different:
captions sit higher off the bottom edge (bigger MarginV) so UI overlays and the
progress bar don't cover them, and text is a touch larger for small screens.
"""

from captr.ass import StyleSpec

# Clean subtitles, raised into the vertical safe area.
FILM_VERTICAL = StyleSpec(
    name="FilmVertical",
    fontname="DejaVu Sans",
    fontsize=46,
    primary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H96000000",
    bold=0,
    outline=1.8,
    shadow=0.8,
    alignment=2,
    margin_l=60,
    margin_r=60,
    margin_v=220,          # well above the bottom UI zone
)

# Animated word-by-word, sized and raised for vertical video.
POP_VERTICAL = StyleSpec(
    name="PopVertical",
    fontname="DejaVu Sans",
    fontsize=72,
    primary_colour="&H0000F0FF",
    secondary_colour="&H00FFFFFF",
    outline_colour="&H00000000",
    back_colour="&H50000000",
    bold=-1,
    outline=3.2,
    shadow=1.0,
    alignment=2,
    margin_l=60,
    margin_r=60,
    margin_v=320,          # sits high in the 9:16 frame, clear of the bottom UI
    word_level=True,
)
