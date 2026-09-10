# Build context must be the repo root (not services/feasibility/): seed_loader.py
# reads data/seed/ three directories above itself, so this image keeps repo-root
# data/ alongside the service code at the same relative depth.
FROM python:3.12-slim

COPY services/feasibility/requirements.txt /app/services/feasibility/requirements.txt
RUN pip install --no-cache-dir -r /app/services/feasibility/requirements.txt

COPY services/feasibility/ /app/services/feasibility/
COPY data/ /app/data/

WORKDIR /app/services/feasibility

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
