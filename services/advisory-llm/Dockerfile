FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the local scheme-match and chatbot-intent classifiers at build time.
# These are real, deterministic training runs (fixed RNG seeds — see
# train/generate_training_data.py and train/*.py) that finish in well under a
# minute on CPU. Nothing here calls out to a network or an external API. The
# resulting models/*.joblib artifacts are what app/scheme_match.py and
# app/local_advisor.py load at request time; they are intentionally NOT
# committed to git (binary, and trivially reproducible from these three
# commands), so every image build regenerates them fresh.
RUN python train/generate_training_data.py \
    && python train/train_scheme_match.py \
    && python train/train_local_advisor.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
