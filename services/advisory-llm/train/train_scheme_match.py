"""Trains the scheme-match classifier on training_data.csv (see
generate_training_data.py) and writes:
  - ../models/scheme_match.joblib   (the fitted sklearn Pipeline)
  - ../models/scheme_match_report.txt (accuracy, F1, confusion matrix, feature importances)

Run: python train_scheme_match.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
MODELS_DIR = HERE.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

NUMERIC_FEATURES = [
    "years_operating", "annual_family_income", "monthly_revenue",
    "requested_amount", "margin_capital",
]
CATEGORICAL_FEATURES = ["category", "gender", "location_type"]
BOOLEAN_FEATURES = ["is_new_business", "is_sc_st"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES


def main() -> None:
    df = pd.read_csv(HERE / "training_data.csv")
    df["is_new_business"] = df["is_new_business"].astype(int)
    df["is_sc_st"] = df["is_sc_st"].astype(int)

    X = df[FEATURE_COLUMNS]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",  # numeric + boolean features pass through as-is
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=14,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("classifier", clf)])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    cv_scores = cross_val_score(pipeline, X, y, cv=5, n_jobs=-1)

    report_lines = []
    report_lines.append("Scheme-Match Classifier -- Training Report")
    report_lines.append("=" * 50)
    report_lines.append(f"Train rows: {len(X_train)}  Test rows: {len(X_test)}")
    report_lines.append(f"Holdout accuracy: {accuracy:.4f}")
    report_lines.append(f"Holdout macro F1: {f1_macro:.4f}")
    report_lines.append(f"5-fold CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    report_lines.append("")
    report_lines.append("Classification report:")
    report_lines.append(classification_report(y_test, y_pred))
    report_lines.append("Confusion matrix (rows=true, cols=predicted):")
    labels_sorted = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels_sorted)
    report_lines.append(f"labels: {labels_sorted}")
    for row_label, row in zip(labels_sorted, cm):
        report_lines.append(f"  {row_label:20s} {row.tolist()}")

    # Feature importances, mapped back to human-readable names (one-hot columns
    # get their original categorical column name folded back in for readability).
    ohe = pipeline.named_steps["preprocess"].named_transformers_["cat"]
    cat_names = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
    passthrough_names = NUMERIC_FEATURES + BOOLEAN_FEATURES
    all_feature_names = cat_names + passthrough_names
    importances = pipeline.named_steps["classifier"].feature_importances_

    grouped_importance: dict[str, float] = {}
    for name, importance in zip(all_feature_names, importances):
        base = name.split("_")[0] if name in cat_names else name
        # Fold one-hot columns for the same original feature back together.
        for orig in CATEGORICAL_FEATURES:
            if name.startswith(orig + "_"):
                base = orig
                break
        grouped_importance[base] = grouped_importance.get(base, 0.0) + float(importance)

    report_lines.append("")
    report_lines.append("Feature importances (grouped back to original features):")
    for name, importance in sorted(grouped_importance.items(), key=lambda kv: -kv[1]):
        report_lines.append(f"  {name:22s} {importance:.4f}")

    report_text = "\n".join(report_lines)
    print(report_text)

    (MODELS_DIR / "scheme_match_report.txt").write_text(report_text, encoding="utf-8")
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_columns": FEATURE_COLUMNS,
            "classes": list(pipeline.named_steps["classifier"].classes_),
            "grouped_importance": grouped_importance,
        },
        MODELS_DIR / "scheme_match.joblib",
    )
    print(f"\nSaved model to {MODELS_DIR / 'scheme_match.joblib'}")


if __name__ == "__main__":
    main()
