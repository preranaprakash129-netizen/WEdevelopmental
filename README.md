# SIH26091 — AI Business Advisory & Financial Calculator for Rural Micro-Entrepreneurs

Helps rural micro-entrepreneurs assess feasibility, calculate loan/EMI plans under
PMEGP/MUDRA/Stand-Up India, get an Entrepreneurial Sustainability Score (ESS), and chat
with an LLM advisor in their own language.

## Team & ownership

| Folder | Owner | What it does |
|---|---|---|
| `frontend/` | person 5 | React + Tailwind UI |
| `backend-api/` | person 1 | FastAPI gateway/orchestrator |
| `services/feasibility/` | person 2 | Market/SWOT/competitor logic |
| `services/calculator/` | person 3 | EMI, scheme eligibility, scheme router |
| `services/ess-scoring/` | person 4 | ESS sub-models, SHAP, diagnostics |
| `services/advisory-llm/` | person 6 | LangChain intake, RAG over scheme docs, i18n |
| `data/seed/` | shared | Synthetic demo dataset |
| `infra/docker/` | person 1 | Shared docker/infra config |

Ownership is enforced via [`.github/CODEOWNERS`](.github/CODEOWNERS) — update it with real
GitHub usernames as soon as you have them.

**Contract:** [`docs/api-contract.md`](docs/api-contract.md) is the single source of truth
for every request/response shape. Build against it starting now — if you need to change a
field, edit that file in a PR first and flag it to the team before changing your service.

## Branch workflow

1. Branch off `main`: `feature/<name>-<task>` (e.g. `feature/priya-emi-schedule`).
2. **Work only inside your assigned folder.** Don't touch another service's directory —
   if you need a shared type/schema change, edit `docs/api-contract.md` and ping the team.
3. Push early, open a **draft PR** as soon as you have anything running — don't wait until
   it's finished. This lets others see progress and catch contract drift early.
4. Rebase on `main` before marking your PR ready / merging:
   ```
   git fetch origin
   git rebase origin/main
   ```
5. Squash-merge (or your team's preference) once green and reviewed.

## Getting started locally

```bash
cp .env.example .env      # fill in real keys
docker compose up         # brings up postgres + backend-api
```

Each service under `services/*` currently has no Dockerfile yet (see the commented stubs
in `docker-compose.yml`) — until yours has one, run it locally with `uvicorn` (Python
services) or `npm run dev` (frontend) on your assigned port (8001–8004), and point
`backend-api` at `http://localhost:<your-port>` via `.env`.

## Day 1 target

By end of day 1: `docker compose up` brings up the **whole pipeline** end-to-end, even if
every service is returning stub/fake data that matches the shapes in
`docs/api-contract.md`. Getting the plumbing connected early is more valuable than any one
service being "real" — real logic comes on day 2–3.

## Ports

| Service | Port |
|---|---|
| postgres | 5432 |
| backend-api | 8000 |
| feasibility | 8001 |
| calculator | 8002 |
| ess-scoring | 8003 |
| advisory-llm | 8004 |
| frontend (dev server) | 5173 |
