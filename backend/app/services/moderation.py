"""A small profanity filter for everything the participant types.

Words are grouped into three tiers, following the scale Ofcom (the UK broadcast
regulator) uses in its research on offensive language:

- ``mild``     – unlikely to offend most people ("hell", "damn")
- ``moderate`` – clearly rude ("shit", "bastard")
- ``strong``   – highly offensive ("fuck", "cunt")

``CONTENT_FILTER`` in ``.env`` sets the lowest tier that is blocked. The default
is ``mild``, the strictest, because an interview is a professional setting.

Hate, sexual, violent and self-harm content is a different problem from swearing,
and the model provider covers it: Microsoft Foundry's built-in Content Safety
filter blocks those categories at medium severity by default (see
``ContentFiltered`` in ``app/llm/client.py``).

Matching works on whole words, so "hello", "shell" and "Scunthorpe" pass. It
also catches common disguises: any letter case, repeated letters ("fuuuck") and
number-for-letter swaps ("sh1t").
"""

import re
from enum import IntEnum

from app.config import FilterLevel


class Severity(IntEnum):
    MILD = 1
    MODERATE = 2
    STRONG = 3


# A trailing "*" means "this word and any word that starts with it" (fuck → fucking).
WORDS: dict[Severity, list[str]] = {
    Severity.MILD: ["hell", "damn", "dammit", "goddamn*", "crap*", "bloody", "bugger*"],
    Severity.MODERATE: [
        "shit*", "bullshit*", "bitch*", "bastard*", "ass", "asshole*", "arse", "arsehole*",
        "dickhead*", "piss*", "prick", "pricks", "wanker*", "bollocks", "douche*", "twat*",
    ],
    Severity.STRONG: ["fuck*", "motherfuck*", "cunt*"],
}  # fmt: skip

# Number-for-letter swaps, undone before matching.
LEET = str.maketrans("013457@$", "oieastas")


class InappropriateLanguage(ValueError):
    """The text contains a blocked word."""

    def __init__(self, field: str) -> None:
        super().__init__(
            f"Your {field} contains language that isn't allowed here. "
            "It has been cleared. Please rephrase it and try again."
        )


def _pattern(word: str) -> str:
    """'hell' → h+e+l+l+ (so 'heeelll' matches); a trailing * allows any ending."""
    stem = word.rstrip("*")
    letters = "".join(f"{re.escape(c)}+" for c in stem)
    return letters + (r"\w*" if word.endswith("*") else "")


def _compile(severities: list[Severity]) -> re.Pattern[str] | None:
    words = [w for s in severities for w in WORDS[s]]
    if not words:
        return None
    return re.compile(r"\b(?:" + "|".join(_pattern(w) for w in words) + r")\b", re.IGNORECASE)


class ContentFilter:
    def __init__(self, level: FilterLevel = "mild") -> None:
        blocked = [] if level == "off" else [s for s in Severity if s >= Severity[level.upper()]]
        self._regex = _compile(blocked)

    def is_clean(self, text: str) -> bool:
        if self._regex is None:
            return True
        return not self._regex.search(text.translate(LEET))

    def check(self, text: str, *, field: str) -> None:
        """Raise ``InappropriateLanguage`` if ``text`` contains a blocked word."""
        if not self.is_clean(text):
            raise InappropriateLanguage(field)
