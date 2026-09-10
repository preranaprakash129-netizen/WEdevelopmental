"""Fully local advisory chatbot -- no external API call, ever.

Pipeline: TF-IDF + linear SVM (scheme classifier + intent classifier, trained
separately -- see train/train_local_advisor.py for why) routes the question to
a (scheme, intent) pair, then a deterministic template pulls the answer from
scheme_facts.py's structured data. There is no generative model anywhere in
this path, so there is no hallucination risk: every number in every answer
traces back to a verifiable field in scheme_facts.py, not to a model's guess.

This is ADVISORY_MODE=local_ml -- the default. ADVISORY_MODE=rag (the
Claude-API pipeline in advisor.py) and ADVISORY_MODE=mock still exist for
comparison/fallback, but this is the one built to not depend on any third
party at inference time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib

from .scheme_facts import SCHEMES, SchemeFacts

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "local_advisor.joblib"
CONFIDENCE_FLOOR = 0.18  # below this, be honest rather than guess

_bundle = None


def _load() -> dict:
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"{MODEL_PATH} not found -- run `python train/train_local_advisor.py` "
                f"from services/advisory-llm/ first."
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def is_model_available() -> bool:
    return MODEL_PATH.exists()


def _top_prediction(pipeline, text: str) -> Tuple[str, float]:
    proba = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    best_idx = proba.argmax()
    return classes[best_idx], float(proba[best_idx])


def _fmt_money(amount: int) -> str:
    if amount >= 10_000_000:
        return f"Rs.{amount / 10_000_000:.1f} crore"
    if amount >= 100_000:
        return f"Rs.{amount / 100_000:.1f} lakh"
    return f"Rs.{amount:,}"


def _answer_eligibility(f: SchemeFacts) -> str:
    parts = [f"{f.display_name}:"]
    if f.women_only:
        parts.append("open only to women entrepreneurs.")
    elif f.requires_sc_st_or_woman:
        parts.append("requires the applicant to be SC/ST or a woman (or, for a company, 51%+ owned by one).")
    else:
        parts.append("open to general applicants, no caste/gender restriction.")
    if f.requires_new_business:
        parts.append("Only for new (greenfield) businesses, not existing ones.")
    else:
        parts.append("Open to both new and existing businesses.")
    if f.allowed_categories:
        parts.append(f"Limited to: {', '.join(f.allowed_categories)}.")
    if f.max_annual_family_income:
        parts.append(
            f"Annual family income must be under {_fmt_money(f.max_annual_family_income)} "
            f"(under {_fmt_money(f.max_annual_family_income_sc_st)} is the limit for SC/ST applicants)."
            if f.max_annual_family_income_sc_st
            else f"Annual family income must be under {_fmt_money(f.max_annual_family_income)}."
        )
    return " ".join(parts)


def _answer_amount(f: SchemeFacts) -> str:
    parts = [f"{f.display_name}:"]
    if f.tiers:
        tier_text = "; ".join(f"{name} ({rng})" for name, rng in f.tiers.items())
        parts.append(f"Loan tiers: {tier_text}.")
    else:
        parts.append(f"Loan range: {_fmt_money(f.min_loan)} to {_fmt_money(f.max_loan)}.")
    if f.subsidy_general_pct:
        if f.subsidy_special_pct and f.subsidy_special_pct != f.subsidy_general_pct:
            parts.append(
                f"Subsidy: {f.subsidy_general_pct:.0f}% general category, "
                f"{f.subsidy_special_pct:.0f}% special category."
            )
        else:
            parts.append(f"Subsidy: {f.subsidy_general_pct:.0f}%.")
    if f.guarantee_coverage_pct_general:
        parts.append(
            f"Guarantee coverage: {f.guarantee_coverage_pct_general:.0f}% general, "
            f"up to {f.guarantee_coverage_pct_special:.0f}% for priority categories."
        )
    if f.own_contribution_pct_general:
        parts.append(
            f"Your own contribution: {f.own_contribution_pct_general:.0f}% general category, "
            f"{f.own_contribution_pct_special:.0f}% special category."
        )
    return " ".join(parts)


def _answer_documents(f: SchemeFacts) -> str:
    docs = ", ".join(f.documents) if f.documents else "check the scheme portal for the current document list"
    return f"{f.display_name} typically needs: {docs}."


def _answer_apply_process(f: SchemeFacts) -> str:
    return f"{f.display_name}: {f.apply_process}"


_TEMPLATES = {
    "eligibility": _answer_eligibility,
    "amount": _answer_amount,
    "documents": _answer_documents,
    "apply_process": _answer_apply_process,
}

_GREETING_TEXT = (
    "Hi! I can answer questions about PMEGP, MUDRA, Stand-Up India, CGTMSE, PMFME, and "
    "Karnataka's Udyogini scheme -- eligibility, loan/subsidy amounts, required documents, "
    "or how to apply. What would you like to know?"
)

_WHICH_SCHEME_TEXT = (
    "I can point you in the right direction if you tell me about a specific scheme, or use "
    "the Scheme Match tool (see the nav bar) which ranks all 6 schemes for your business "
    "profile using a trained model, with a confidence score and reasons for each."
)

_LOW_CONFIDENCE_TEXT = (
    "I don't have a confident answer for that. I can help with eligibility, loan/subsidy "
    "amounts, required documents, or the application process for PMEGP, MUDRA, Stand-Up "
    "India, CGTMSE, PMFME, or Karnataka's Udyogini scheme -- try asking about one of those."
)


def _fmt_money_kn(amount: int) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.1f} ಕೋಟಿ"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.1f} ಲಕ್ಷ"
    return f"₹{amount:,}"


def _answer_eligibility_kn(f: SchemeFacts) -> str:
    parts = [f"{f.display_name}:"]
    if f.women_only:
        parts.append("ಕೇವಲ ಮಹಿಳಾ ಉದ್ಯಮಿಗಳಿಗೆ ಮಾತ್ರ.")
    elif f.requires_sc_st_or_woman:
        parts.append("ಅರ್ಜಿದಾರರು SC/ST ಅಥವಾ ಮಹಿಳೆಯಾಗಿರಬೇಕು (ಕಂಪನಿಯಾದರೆ, ಅದರಲ್ಲಿ 51%+ ಪಾಲು ಅವರದ್ದಾಗಿರಬೇಕು).")
    else:
        parts.append("ಸಾಮಾನ್ಯ ಅರ್ಜಿದಾರರಿಗೆ ಮುಕ್ತ, ಜಾತಿ/ಲಿಂಗ ನಿರ್ಬಂಧವಿಲ್ಲ.")
    if f.requires_new_business:
        parts.append("ಹೊಸ (ಗ್ರೀನ್‌ಫೀಲ್ಡ್) ವ್ಯಾಪಾರಗಳಿಗೆ ಮಾತ್ರ, ಈಗಾಗಲೇ ಇರುವ ವ್ಯಾಪಾರಗಳಿಗಲ್ಲ.")
    else:
        parts.append("ಹೊಸ ಮತ್ತು ಈಗಾಗಲೇ ಇರುವ ಎರಡೂ ವ್ಯಾಪಾರಗಳಿಗೆ ಮುಕ್ತ.")
    if f.allowed_categories:
        parts.append(f"ಇವುಗಳಿಗೆ ಮಾತ್ರ ಸೀಮಿತ: {', '.join(f.allowed_categories)}.")
    if f.max_annual_family_income:
        parts.append(
            f"ವಾರ್ಷಿಕ ಕುಟುಂಬ ಆದಾಯ {_fmt_money_kn(f.max_annual_family_income)} ಗಿಂತ ಕಡಿಮೆ ಇರಬೇಕು "
            f"(SC/ST ಅರ್ಜಿದಾರರಿಗೆ ಮಿತಿ {_fmt_money_kn(f.max_annual_family_income_sc_st)})."
            if f.max_annual_family_income_sc_st
            else f"ವಾರ್ಷಿಕ ಕುಟುಂಬ ಆದಾಯ {_fmt_money_kn(f.max_annual_family_income)} ಗಿಂತ ಕಡಿಮೆ ಇರಬೇಕು."
        )
    return " ".join(parts)


def _answer_amount_kn(f: SchemeFacts) -> str:
    parts = [f"{f.display_name}:"]
    if f.tiers:
        tier_text = "; ".join(f"{name} ({rng})" for name, rng in f.tiers.items())
        parts.append(f"ಸಾಲದ ಹಂತಗಳು: {tier_text}.")
    else:
        parts.append(f"ಸಾಲದ ವ್ಯಾಪ್ತಿ: {_fmt_money_kn(f.min_loan)} ರಿಂದ {_fmt_money_kn(f.max_loan)}.")
    if f.subsidy_general_pct:
        if f.subsidy_special_pct and f.subsidy_special_pct != f.subsidy_general_pct:
            parts.append(
                f"ಸಬ್ಸಿಡಿ: ಸಾಮಾನ್ಯ ವರ್ಗಕ್ಕೆ {f.subsidy_general_pct:.0f}%, "
                f"ವಿಶೇಷ ವರ್ಗಕ್ಕೆ {f.subsidy_special_pct:.0f}%."
            )
        else:
            parts.append(f"ಸಬ್ಸಿಡಿ: {f.subsidy_general_pct:.0f}%.")
    if f.guarantee_coverage_pct_general:
        parts.append(
            f"ಗ್ಯಾರಂಟಿ ವ್ಯಾಪ್ತಿ: ಸಾಮಾನ್ಯಕ್ಕೆ {f.guarantee_coverage_pct_general:.0f}%, "
            f"ಆದ್ಯತಾ ವರ್ಗಗಳಿಗೆ {f.guarantee_coverage_pct_special:.0f}% ವರೆಗೆ."
        )
    if f.own_contribution_pct_general:
        parts.append(
            f"ನಿಮ್ಮ ಸ್ವಂತ ಕೊಡುಗೆ: ಸಾಮಾನ್ಯ ವರ್ಗಕ್ಕೆ {f.own_contribution_pct_general:.0f}%, "
            f"ವಿಶೇಷ ವರ್ಗಕ್ಕೆ {f.own_contribution_pct_special:.0f}%."
        )
    return " ".join(parts)


def _answer_documents_kn(f: SchemeFacts) -> str:
    docs = ", ".join(f.documents) if f.documents else "ಪ್ರಸ್ತುತ ದಾಖಲೆಗಳ ಪಟ್ಟಿಗಾಗಿ ಯೋಜನಾ ಪೋರ್ಟಲ್ ಪರಿಶೀಲಿಸಿ"
    return f"{f.display_name} ಗೆ ಸಾಮಾನ್ಯವಾಗಿ ಬೇಕಾಗುವುದು: {docs}."


def _answer_apply_process_kn(f: SchemeFacts) -> str:
    return f"{f.display_name}: {f.apply_process}"


_TEMPLATES_KN = {
    "eligibility": _answer_eligibility_kn,
    "amount": _answer_amount_kn,
    "documents": _answer_documents_kn,
    "apply_process": _answer_apply_process_kn,
}

_GREETING_TEXT_KN = (
    "ನಮಸ್ಕಾರ! ನಾನು PMEGP, MUDRA, Stand-Up India, CGTMSE, PMFME, ಮತ್ತು ಕರ್ನಾಟಕದ "
    "ಉದ್ಯೋಗಿನಿ ಯೋಜನೆಯ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಬಲ್ಲೆ -- ಅರ್ಹತೆ, ಸಾಲ/ಸಬ್ಸಿಡಿ ಮೊತ್ತ, ಬೇಕಾದ "
    "ದಾಖಲೆಗಳು, ಅಥವಾ ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ. ನಿಮಗೆ ಏನು ತಿಳಿಯಬೇಕು?"
)

_WHICH_SCHEME_TEXT_KN = (
    "ನೀವು ಒಂದು ನಿರ್ದಿಷ್ಟ ಯೋಜನೆಯ ಬಗ್ಗೆ ಹೇಳಿದರೆ ನಾನು ಸರಿಯಾದ ದಿಕ್ಕು ತೋರಿಸಬಲ್ಲೆ, ಅಥವಾ "
    "ನ್ಯಾವ್ ಬಾರ್‌ನಲ್ಲಿರುವ 'Scheme Match' ಪರಿಕರ ಬಳಸಿ -- ಇದು ತರಬೇತಿ ಪಡೆದ ಮಾದರಿಯನ್ನು ಬಳಸಿ ಎಲ್ಲಾ "
    "6 ಯೋಜನೆಗಳನ್ನು ನಿಮ್ಮ ವ್ಯಾಪಾರ ಪ್ರೊಫೈಲ್‌ಗೆ ಅನುಗುಣವಾಗಿ ಶ್ರೇಣೀಕರಿಸುತ್ತದೆ, ವಿಶ್ವಾಸ ಅಂಕ ಮತ್ತು "
    "ಕಾರಣಗಳೊಂದಿಗೆ."
)

_LOW_CONFIDENCE_TEXT_KN = (
    "ಇದಕ್ಕೆ ನನ್ನ ಬಳಿ ಖಚಿತ ಉತ್ತರವಿಲ್ಲ. PMEGP, MUDRA, Stand-Up India, CGTMSE, PMFME, ಅಥವಾ "
    "ಕರ್ನಾಟಕದ ಉದ್ಯೋಗಿನಿ ಯೋಜನೆಯ ಅರ್ಹತೆ, ಸಾಲ/ಸಬ್ಸಿಡಿ ಮೊತ್ತ, ಬೇಕಾದ ದಾಖಲೆಗಳು, ಅಥವಾ ಅರ್ಜಿ "
    "ಪ್ರಕ್ರಿಯೆಯ ಬಗ್ಗೆ ಕೇಳಿ ನೋಡಿ."
)


def answer(message: str, language: str = "en") -> Dict:
    """Returns {response_text, cited_sources, detected_scheme, detected_intent,
    scheme_confidence, intent_confidence} -- no network call, no external API.
    `language`: "kn" for Kannada answer templates, anything else falls back to
    English -- the scheme/intent classifiers themselves are language-agnostic
    (trained on English question text) and still route Kannada or Hinglish
    questions reasonably via shared loanwords/scheme names, but the *answer
    templates* only exist in these two languages so far."""
    bundle = _load()
    scheme, scheme_conf = _top_prediction(bundle["scheme_pipeline"], message)
    intent, intent_conf = _top_prediction(bundle["intent_pipeline"], message)

    kn = language == "kn"
    templates = _TEMPLATES_KN if kn else _TEMPLATES
    greeting_text = _GREETING_TEXT_KN if kn else _GREETING_TEXT
    which_scheme_text = _WHICH_SCHEME_TEXT_KN if kn else _WHICH_SCHEME_TEXT
    low_confidence_text = _LOW_CONFIDENCE_TEXT_KN if kn else _LOW_CONFIDENCE_TEXT

    if intent == "unclear":
        return _result(low_confidence_text, [], scheme, intent, scheme_conf, intent_conf)

    if intent == "greeting" and intent_conf >= CONFIDENCE_FLOOR:
        return _result(greeting_text, [], scheme, intent, scheme_conf, intent_conf)

    if intent == "which_scheme" and intent_conf >= CONFIDENCE_FLOOR:
        return _result(which_scheme_text, [], scheme, intent, scheme_conf, intent_conf)

    if scheme == "GENERAL" or scheme not in SCHEMES or intent not in templates:
        if scheme_conf < CONFIDENCE_FLOOR and intent_conf < CONFIDENCE_FLOOR:
            return _result(low_confidence_text, [], scheme, intent, scheme_conf, intent_conf)

    if scheme in SCHEMES and intent in templates:
        facts = SCHEMES[scheme]
        text = templates[intent](facts)
        sources = [{"scheme": facts.key, "document": facts.display_name, "url": facts.url}]
        return _result(text, sources, scheme, intent, scheme_conf, intent_conf)

    return _result(low_confidence_text, [], scheme, intent, scheme_conf, intent_conf)


def _result(text: str, sources: List[dict], scheme: str, intent: str, scheme_conf: float, intent_conf: float) -> Dict:
    return {
        "response_text": text,
        "cited_sources": sources,
        "detected_scheme": scheme,
        "detected_intent": intent,
        "scheme_confidence": round(scheme_conf, 4),
        "intent_confidence": round(intent_conf, 4),
    }
