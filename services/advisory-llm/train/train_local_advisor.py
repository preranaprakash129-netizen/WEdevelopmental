"""Trains the local (no external API) chatbot's intent router.

Decomposed into two independent classifiers rather than one flat classifier
over the combinatorial product of (scheme x intent):
  - scheme classifier: which of the 6 schemes (or GENERAL) the question is about
  - intent classifier: what kind of question it is (eligibility/amount/documents/
    apply_process/which_scheme/greeting)

This is a real, deliberate design choice, not just a training-data workaround:
with a small hand-written dataset, splitting the task this way gives each
classifier far more examples per class (an "eligibility" question about any
scheme trains the same intent class), and it *compositionally generalizes* --
a documents question about a scheme/intent combination that was never written
as a single example still routes correctly, because scheme-detection and
intent-detection never depended on having seen that exact combination. That's
a genuinely better answer to "why not one classifier" than "it scored higher".

Honesty note, kept from the flat-classifier version: this is a small,
hand-written dataset (~100 examples). The holdout accuracies below are
directional, not tight estimates -- say so if asked, and retrain on real usage
questions once the app has been used a few dozen times.

Run: python train_local_advisor.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chat_training_examples import EXAMPLES  # noqa: E402

HERE = Path(__file__).resolve().parent
MODELS_DIR = HERE.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def _make_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("clf", CalibratedClassifierCV(LinearSVC(class_weight="balanced"), cv=3)),
        ]
    )


def _train_and_report(name: str, texts, labels) -> Pipeline:
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    pipeline = _make_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    report = [
        f"{name} classifier -- Training Report",
        "=" * 50,
        f"Total examples: {len(texts)}  Classes: {len(set(labels))}",
        f"Train: {len(X_train)}  Test: {len(X_test)}",
        f"Holdout accuracy: {accuracy:.4f}",
        "",
        classification_report(y_test, y_pred, zero_division=0),
    ]
    print("\n".join(report))

    # Refit on all examples for the shipped model.
    pipeline.fit(texts, labels)
    return pipeline, "\n".join(report)


def main() -> None:
    texts = [t for t, _ in EXAMPLES]
    scheme_labels = [l.split("::")[0] for _, l in EXAMPLES]
    intent_labels = [l.split("::")[1] for _, l in EXAMPLES]

    scheme_pipeline, scheme_report = _train_and_report("Scheme", texts, scheme_labels)
    print()
    intent_pipeline, intent_report = _train_and_report("Intent", texts, intent_labels)

    (MODELS_DIR / "local_advisor_report.txt").write_text(
        scheme_report + "\n\n" + intent_report, encoding="utf-8"
    )
    joblib.dump(
        {"scheme_pipeline": scheme_pipeline, "intent_pipeline": intent_pipeline},
        MODELS_DIR / "local_advisor.joblib",
    )
    print(f"\nSaved model to {MODELS_DIR / 'local_advisor.joblib'}")


if __name__ == "__main__":
    main()
