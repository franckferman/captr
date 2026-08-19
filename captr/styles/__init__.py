#!/usr/bin/env python3
# captr/styles/__init__.py

"""
Style presets registry.

Each preset is a StyleSpec (see captr.ass). A preset with word_level=True (the
'pop' family) renders per-word karaoke and makes captr request word timestamps
from whispr automatically.
"""

from captr.ass import StyleSpec
from captr.styles.film import FILM
from captr.styles.translation import TRANSLATION
from captr.styles.pop import POP
from captr.styles.vertical import FILM_VERTICAL, POP_VERTICAL

STYLES = {
    "film": FILM,
    "translation": TRANSLATION,
    "pop": POP,
    "film-vertical": FILM_VERTICAL,
    "pop-vertical": POP_VERTICAL,
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
