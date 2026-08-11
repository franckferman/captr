#!/usr/bin/env python3
# captr/styles/translation.py

"""
'translation' preset — like 'film' but tuned for translated subtitles.

Slightly smaller and a touch more transparent shadow, so translated lines read
as a discreet overlay rather than the primary content. Pairs with whispr's
--translate-to output.
"""

from captr.ass import StyleSpec

TRANSLATION = StyleSpec(
    name="Translation",
    fontname="DejaVu Sans",
    fontsize=38,
    primary_colour="&H00F0F0F0",   # near-white
    outline_colour="&H00000000",
    back_colour="&HB4000000",      # ~70% black shadow
    bold=0,
    outline=1.4,
    shadow=0.6,
    alignment=2,
    margin_v=42,
)
