"""Contract-shaped canned responses for `ADVISORY_MODE=mock`.

This is what the gateway and frontend code against until the corpus is ingested.
Two rules keep the mock from becoming a liability:

* The text is **procedural only** — no subsidy percentages, loan ceilings or
  tenure figures. Every number in this service has to come from a retrieved
  document, so there are no plausible-looking numbers here for someone to
  screenshot into a slide by mistake.
* Citation metadata comes from `corpus/manifest.json`, the same place the real
  pipeline gets it, so a mock `cited_sources` entry is byte-identical to a real
  one for the same document.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .manifest import ManifestEntry, find_by_scheme, load_manifest

# Used only if corpus/manifest.json is unreadable (e.g. a container that mounted
# a different corpus dir). Mirrors the manifest committed to the repo.
_FALLBACK_SOURCES: Dict[str, Tuple[str, str]] = {
    "PMEGP": ("PMEGP Guidelines", "https://kviconline.gov.in/pmegp"),
    "MUDRA": ("Pradhan Mantri MUDRA Yojana", "https://www.mudra.org.in/"),
}

# Keyword -> scheme. Matched against the lowercased message; first hit wins.
_SCHEME_KEYWORDS: Tuple[Tuple[str, str], ...] = (
    ("pmegp", "PMEGP"),
    ("khadi", "PMEGP"),
    ("kvic", "PMEGP"),
    ("mudra", "MUDRA"),
    ("shishu", "MUDRA"),
    ("kishor", "MUDRA"),
    ("tarun", "MUDRA"),
)

_ANSWERS: Dict[Optional[str], Dict[str, str]] = {
    "PMEGP": {
        "en": (
            "For PMEGP you apply online through the KVIC portal, and your application is "
            "routed to your district's KVIC, KVIB or DIC office. Keep your Aadhaar, PAN, a "
            "project report for the unit you want to set up, and your education and category "
            "certificates ready. After the district task force interview, the sanctioning "
            "bank runs its own appraisal before anything is disbursed."
        ),
        "hi": (
            "PMEGP के लिए आप KVIC पोर्टल के माध्यम से ऑनलाइन आवेदन कर सकते हैं, और आपका आवेदन "
            "आपके ज़िले के KVIC, KVIB या DIC कार्यालय को भेजा जाता है। आधार, पैन, प्रस्तावित इकाई की "
            "प्रोजेक्ट रिपोर्ट तथा शिक्षा और श्रेणी से जुड़े प्रमाण पत्र तैयार रखें। ज़िला टास्क फोर्स "
            "के साक्षात्कार के बाद बैंक अपना मूल्यांकन करता है, उसके बाद ही राशि जारी होती है।"
        ),
    },
    "MUDRA": {
        "en": (
            "MUDRA loans are given by banks, NBFCs and microfinance institutions rather than "
            "by MUDRA itself, so you apply at the branch where you already hold an account. "
            "The scheme is organised in three stages — Shishu, Kishore and Tarun — and which "
            "one your application falls under depends on how much your business needs. Carry "
            "identity and address proof, proof of your business address, and your last six "
            "months of bank statements."
        ),
        "hi": (
            "मुद्रा ऋण सीधे मुद्रा से नहीं, बल्कि बैंकों, एनबीएफसी और सूक्ष्म वित्त संस्थानों के माध्यम से "
            "मिलता है, इसलिए आवेदन उसी शाखा में करें जहाँ आपका खाता पहले से है। योजना तीन चरणों — "
            "शिशु, किशोर और तरुण — में बंटी है, और आपका आवेदन किस चरण में आएगा यह आपकी ऋण "
            "आवश्यकता पर निर्भर करता है। पहचान व पते का प्रमाण, व्यवसाय के पते का प्रमाण और पिछले "
            "छह महीनों का बैंक विवरण साथ रखें।"
        ),
    },
    None: {
        "en": (
            "I can help you work through government scheme options for your business — PMEGP "
            "and MUDRA are the two I have detailed guidance on right now. Tell me what you "
            "want to start or expand, roughly how much you need, and how much of your own "
            "capital you can put in, and I'll narrow it down."
        ),
        "hi": (
            "मैं आपके व्यवसाय के लिए सरकारी योजनाओं के विकल्प चुनने में मदद कर सकता हूँ — फ़िलहाल "
            "PMEGP और मुद्रा योजना पर मेरे पास विस्तृत जानकारी है। बताइए आप क्या शुरू या विस्तार "
            "करना चाहते हैं, लगभग कितनी राशि की ज़रूरत है, और आप अपनी ओर से कितनी पूँजी लगा "
            "सकते हैं।"
        ),
    },
}


def detect_scheme(message: str) -> Optional[str]:
    lowered = message.lower()
    for keyword, scheme in _SCHEME_KEYWORDS:
        if keyword in lowered:
            return scheme
    return None


def mock_answer(message: str, language: str, manifest_path: Path) -> Tuple[str, List[dict]]:
    """Return ``(response_text, cited_sources)`` for a mock reply.

    Languages other than English and Hindi fall back to the English text while
    still reporting the language we actually detected — an honest mock, rather
    than one that pretends we already translate into ten languages.
    """
    scheme = detect_scheme(message)
    by_language = _ANSWERS[scheme]
    text = by_language.get(language, by_language["en"])

    if scheme is None:
        # No scheme in the question yet, so nothing to cite. Exercises the
        # contract's "may be empty array" branch on the gateway and frontend.
        return text, []

    return text, [_source_for(scheme, manifest_path)]


def _source_for(scheme: str, manifest_path: Path) -> dict:
    entry: Optional[ManifestEntry] = find_by_scheme(load_manifest(manifest_path), scheme)
    if entry is not None:
        source = {"scheme": entry.scheme, "document": entry.document}
        if entry.url:
            source["url"] = entry.url
        return source

    document, url = _FALLBACK_SOURCES[scheme]
    return {"scheme": scheme, "document": document, "url": url}
