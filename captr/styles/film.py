#!/usr/bin/env python3
# captr/styles/film.py

"""
'film' preset — clean cinematic subtitles.

Bottom-centred, restrained sans-serif, white with a thin black outline and a
soft shadow. The look you expect on a movie or a documentary: legible, out of
the way, not shouting.
"""

from captr.ass import StyleSpec

FILM = StyleSpec(
    name="Film",
    fontname="DejaVu Sans",
    fontsize=42,
    primary_colour="&H00FFFFFF",   # white
    outline_colour="&H00000000",   # black outline
    back_colour="&H96000000",      # ~60% black shadow
    bold=0,
    outline=1.6,
    shadow=0.8,
    alignment=2,                   # bottom-centre
    margin_v=48,
)
