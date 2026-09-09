# services/advisory-llm

Owner: person 6 (Vamshi)

Intake conversation, RAG over government scheme documents with cited sources, and the
multilingual output pipeline. Implements `POST /advisory-chat` — see
[`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```

Defaults to **mock mode**: contract-shaped canned answers, no API key, no corpus, no
network. That is what `backend-api` and the frontend should code against until the
corpus is ingested.

```bash
curl -s localhost:8004/advisory-chat -H 'content-type: application/json' \
  -d '{"message":"PMEGP ke liye kaise apply karein?","context":{"conversation_id":"conv_8841"}}'
```

`GET /debug/status` reports which mode you're in and how many chunks are ingested — use
it before demoing so nobody mistakes a mock answer for a retrieved one.

## Two modes

| | `ADVISORY_MODE=mock` (default) | `ADVISORY_MODE=rag` |
|---|---|---|
| Answer | Canned, procedural, **no numbers** | Claude, grounded in retrieved extracts |
| `cited_sources` | From `corpus/manifest.json` | From the chunks the model actually cited |
| Needs | Nothing | Credentials + an ingested corpus |

Mock answers deliberately contain no subsidy percentages, loan ceilings or tenures.
Every number this service emits has to come from a retrieved document, so there are no
plausible-looking fake figures lying around to end up in a slide by accident.

`rag` mode with no corpus ingested still answers — it says the scheme documents don't
cover the question and returns `cited_sources: []`. It never falls back to the model's
own memory of these schemes.

See [`.env.example`](.env.example) for every environment variable.

## Ingesting scheme documents

First pass is **PMEGP + MUDRA**. The RBI MSME restructuring circular is deliberately
deferred — it's the densest of the three and worth doing once chunking is proven.

1. Download the official PDFs.
2. Save them in `corpus/pdfs/` under the `source_pdf` filenames in
   [`corpus/manifest.json`](corpus/manifest.json).
3. In the manifest, set `document` to the title printed on the PDF (including its
   year/revision) and `pdf_url` to the exact link you downloaded from.
4. `python -m app.ingest` (or `--scheme PMEGP` for one at a time).
5. `ADVISORY_MODE=rag uvicorn app.main:app --reload --port 8004`

PDFs and the generated `chunks.jsonl` are gitignored. The manifest is what we version,
so anyone on the team can rebuild an identical corpus from the official sources.

## How grounding works

The model is not asked for prose that we then attribute to a document. It's asked for a
structured answer — `{answer, cited_chunk_ids, grounded}` — over numbered extracts, and
`cited_sources` is built by mapping those ids back to their documents. Three
consequences:

- A chunk id the model invents matches nothing and is silently dropped.
- An answer the extracts don't support comes back `grounded: false`, which forces
  `cited_sources: []` rather than a confident guess about someone's loan eligibility.
- Citations dedupe per document, so two chunks of the same PDF are one source.

Chunks carry their page number, so a citation traces back to a page of the original
circular — the difference between "the model said so" and something a judge can check.

Retrieval is **BM25 keyword** (`rank_bm25`), not embeddings: no model download, runs
offline, and it's deterministic enough to explain on stage. `retrieval.Retriever` is the
seam — swapping in a vector or hybrid retriever doesn't touch `advisor.py`.

## Language handling

`detect_language` is a two-stage heuristic: Unicode script first, then a romanized-Hindi
marker check — the contract's own example (`"PMEGP ke liye kaise apply karein?"`) is
Latin-script Hindi and has to come back as `"hi"`. An explicit `language` in the request
always wins over detection.

By default Claude answers **directly** in the detected language; there's no translation
round trip, which keeps terms like "margin money" and "moratorium" intact.
`BhashiniTranslator` is an explicit stub — setting `BHASHINI_API_KEY` switches the
pipeline to generate in English and translate, and the stub will raise until it's
implemented. Leave it unset.

## Notes for the rest of the team

- This service never calls `feasibility`, `calculator` or `ess-scoring` — per the
  contract's Orchestration section, `backend-api` passes anything we need inline.
- `context.conversation_id` continuity is in-process memory
  (`app/conversation.py`), which is fine for a single uvicorn worker. It's the one module
  to swap if we need continuity across restarts or replicas.
- LangChain is used for document splitting; model calls go through the official
  `anthropic` SDK directly rather than a wrapper.
- `docker-compose.yml` still has this service commented out. The `Dockerfile` is here and
  works — uncommenting that block is a one-line change on the gateway owner's side.

## Tests

```bash
pytest
```

Covers the contract shape (including the empty-`cited_sources` branch and the error
shape), language detection, BM25 retrieval, and RAG assembly with the model call
monkeypatched. No test hits the network.
