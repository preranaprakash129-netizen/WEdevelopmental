"""Language detection and the translation pipeline.

`POST /advisory-chat` must return `detected_language` (ISO 639-1) and answer in
that language. Detection is a two-stage heuristic:

1. Unicode script -> language, which covers anything typed in a native script.
2. A romanized-Hindi (Hinglish) marker check, because the contract's own example
   request — "PMEGP ke liye kaise apply karein?" — is Latin-script Hindi and has
   to come back as ``"hi"``, not ``"en"``.

Both stages are placeholders for Bhashini's language-identification endpoint.
The heuristic is deliberately cheap and offline so the demo never depends on a
third-party call just to label a language.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Protocol

DEFAULT_LANGUAGE = "en"

# ISO 639-1 code -> inclusive Unicode codepoint range of its script. Devanagari is
# shared by Hindi/Marathi/Nepali; we default it to Hindi, which is what the demo
# uses. Distinguishing them is a job for Bhashini's language ID, not for us.
_SCRIPT_RANGES = (
    ("hi", 0x0900, 0x097F),  # Devanagari
    ("bn", 0x0980, 0x09FF),  # Bengali
    ("pa", 0x0A00, 0x0A7F),  # Gurmukhi
    ("gu", 0x0A80, 0x0AFF),  # Gujarati
    ("or", 0x0B00, 0x0B7F),  # Odia
    ("ta", 0x0B80, 0x0BFF),  # Tamil
    ("te", 0x0C00, 0x0C7F),  # Telugu
    ("kn", 0x0C80, 0x0CFF),  # Kannada
    ("ml", 0x0D00, 0x0D7F),  # Malayalam
)

# Hindi function words as they get typed on a Latin keyboard. Only tokens that
# are not also plausible English words — "loan", "bank" and friends are excluded
# on purpose, since they appear in genuinely English questions too.
_HINGLISH_MARKERS = frozenset(
    {
        "aap", "apna", "apne", "chahiye", "hai", "hain", "kab", "kahan", "kaise",
        "kaisa", "kar", "kare", "karein", "karna", "ke", "ki", "kitna", "kitni",
        "kya", "liye", "mein", "mera", "meri", "nahi", "nahin", "sakta", "sakte",
        "yojana",
    }
)

# Two markers, not one: a single "ke" or "hai" inside an otherwise English
# sentence is not enough to switch the whole answer into Hindi.
_HINGLISH_THRESHOLD = 2

_WORD_RE = re.compile(r"[a-z]+")

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "or": "Odia",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}


def detect_language(text: str) -> str:
    """Best-effort ISO 639-1 detection. Never raises; falls back to English."""
    script_hit = _detect_by_script(text)
    if script_hit is not None:
        return script_hit
    if _looks_like_romanized_hindi(text):
        return "hi"
    return DEFAULT_LANGUAGE


def _detect_by_script(text: str) -> Optional[str]:
    counts: Dict[str, int] = {}
    for char in text:
        code = ord(char)
        for language, start, end in _SCRIPT_RANGES:
            if start <= code <= end:
                counts[language] = counts.get(language, 0) + 1
                break
    if not counts:
        return None
    return max(counts.items(), key=lambda pair: pair[1])[0]


def _looks_like_romanized_hindi(text: str) -> bool:
    words = _WORD_RE.findall(text.lower())
    hits = sum(1 for word in words if word in _HINGLISH_MARKERS)
    return hits >= _HINGLISH_THRESHOLD


def language_name(code: str) -> str:
    """Human-readable name for the prompt. Unknown codes pass through as-is."""
    return LANGUAGE_NAMES.get(code, code)


class Translator(Protocol):
    # The language the answer is generated in before translation, or None to
    # generate directly in the user's language and skip translation entirely.
    pivot_language: Optional[str]

    def translate(self, text: str, *, source: str, target: str) -> str: ...


class PassthroughTranslator:
    """Returns text unchanged.

    The default path does not translate at all: we ask Claude to answer directly
    in the detected language, which keeps scheme terminology intact (a
    round-trip through a general-purpose MT model tends to mangle "margin money"
    and "moratorium"). This translator exists so the pipeline has the same shape
    whether or not Bhashini is configured.
    """

    pivot_language: Optional[str] = None

    def translate(self, text: str, *, source: str, target: str) -> str:
        return text


class BhashiniTranslator:
    """Bhashini (ULCA) translation — NOT IMPLEMENTED YET.

    Kept as an explicit stub rather than a guess at the wire format. Wiring it up
    is two calls: ``POST`` to the ULCA pipeline-config endpoint to resolve a
    translation service ID for the source/target pair, then ``POST`` to the
    returned compute endpoint with the text. Both need the credentials issued
    with ``BHASHINI_API_KEY``.

    Turn this on only once the direct-answer path is demo-solid — it is the
    fallback for languages Claude handles less fluently, not the primary path.
    """

    # Generate in English, then translate — Bhashini's models are trained on
    # English as the pivot for Indic pairs.
    pivot_language: Optional[str] = "en"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def translate(self, text: str, *, source: str, target: str) -> str:
        raise NotImplementedError(
            "BhashiniTranslator is a stub. Unset BHASHINI_API_KEY to fall back to "
            "PassthroughTranslator, which is the supported path today."
        )


def get_translator(bhashini_api_key: Optional[str]) -> Translator:
    if bhashini_api_key:
        return BhashiniTranslator(bhashini_api_key)
    return PassthroughTranslator()
