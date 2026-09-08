# services/advisory-llm

Owner: person 6

LangChain intake, RAG over scheme documents, i18n (incl. Bhashini integration).
Implements `POST /advisory-chat` — see [`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```
