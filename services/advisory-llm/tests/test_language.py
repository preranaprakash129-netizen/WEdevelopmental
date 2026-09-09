import pytest

from app.language import (
    BhashiniTranslator,
    PassthroughTranslator,
    detect_language,
    get_translator,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("How do I apply for a MUDRA loan?", "en"),
        # The contract's own example is romanized Hindi and must not read as English.
        ("PMEGP ke liye kaise apply karein?", "hi"),
        ("पीएमईजीपी के लिए आवेदन कैसे करें?", "hi"),
        ("মুদ্রা ঋণের জন্য আবেদন কীভাবে করব?", "bn"),
        ("முத்ரா கடனுக்கு எப்படி விண்ணப்பிப்பது?", "ta"),
    ],
)
def test_detect_language(text, expected):
    assert detect_language(text) == expected


def test_single_hinglish_marker_does_not_flip_an_english_sentence():
    # "ki" appears here, but the sentence is plainly English.
    assert detect_language("What is the ki limit for this scheme?") == "en"


def test_empty_message_falls_back_to_english():
    assert detect_language("") == "en"


def test_translator_selection():
    assert isinstance(get_translator(None), PassthroughTranslator)
    assert isinstance(get_translator("some-key"), BhashiniTranslator)


def test_passthrough_translator_skips_translation():
    translator = get_translator(None)
    assert translator.pivot_language is None
    assert translator.translate("unchanged", source="en", target="hi") == "unchanged"


def test_bhashini_translator_is_still_a_stub():
    translator = get_translator("some-key")
    assert translator.pivot_language == "en"
    with pytest.raises(NotImplementedError):
        translator.translate("hello", source="en", target="hi")
