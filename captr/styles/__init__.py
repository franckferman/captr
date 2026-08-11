#!/usr/bin/env python3
# captr/styles/__init__.py

"""
Style presets registry.

Each preset is a StyleSpec (see captr.ass). The 'pop' word-by-word animated
style is planned next and will consume word-level timestamps.
"""

from captr.ass import StyleSpec
from captr.styles.film import FILM
from captr.styles.translation import TRANSLATION

STYLES = {
    "film": FILM,
    "translation": TRANSLATION,
}

DEFAULT_STYLE = "film"


def get_style(name: str) -> StyleSpec:
    """Return the StyleSpec for a preset name, or raise ValueError."""
    try:
        return STYLES[name]
    except KeyError:
        raise ValueError(
            f"Unknown style '{name}'. Available: {sorted(STYLES)}."
        )
