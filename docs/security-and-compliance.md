# Security & Compliance — SIH26091 (prototype status, as of 2026-09-11)

**Status:** honest gap-and-plan statement for a hackathon prototype, not a compliance
certification. Nothing in this document should be presented to judges, users, or
reviewers as a claim that this system is production-ready or DPDP-compliant — it isn't
yet, and this doc says exactly where and why. Anywhere below marked **prototype gap**
means: not implemented, verified by reading the code, not assumed.

There was previously no security/compliance documentation anywhere in this repo — this
is the first pass, written alongside a scoped hardening change to `backend-api/`
(see the PR this doc ships with for the actual diff).

## What's in place today

- **Parameterized SQL throughout.** `backend-api/app/main.py` is the only place in this
  codebase that touches Postgres directly, and every query uses `psycopg2` `%s`
  placeholders — no string-interpolated SQL anywhere in this file. Verified by reading
  every `cur.execute(...)` call, not assumed.
- **Input validation via Pydantic** on the one backend-api route that actually processes
  its input locally rather than just forwarding it (`POST /api/applications` — see
  `CreateApplicationRequest`): length-bounded text fields, `ess_score` bounded to 0–100.
  `services/feasibility`, `services/calculator`, `services/ess-scoring`, and
  `services/advisory-llm` each validate their own request shape via their own Pydantic
  models (`app/schemas.py` in each) — bounds are mostly consistent; a few gaps found and
  left for their respective owners rather than fixed here (see "Known gaps" below), since
  this pass was scoped to `backend-api/` only.
- **CORS locked to known origins**, not `*`. In practice the frontend never makes a
  cross-origin browser request to backend-api at all — both `vite.config.js` (dev) and
  `frontend/nginx.conf` (docker-compose) proxy `/api/*` server-side, so the browser only
  ever sees same-origin requests. The lockdown is still real defense-in-depth against
  some other page calling this API directly from a browser, and is overridable via
  `CORS_ALLOWED_ORIGINS` if the demo runs from a different host.
- **Basic response headers** on every backend-api response: `X-Content-Type-Options:
  nosniff`, `X-Frame-Options: DENY`, and a `Content-Security-Policy: default-src 'none'`
  (correct for a JSON-only API that serves no embeddable content). This does **not**
  cover the frontend's own served HTML/JS — see "Known gaps."
- **No PII/secrets found in logs**, checked by grepping every `logger.*`/`print(`/
  `console.log` call across `backend-api/`, all four `services/*`, and `frontend/src/`.
  The three `logger.exception(...)` calls in `backend-api` use static messages, never
  the request payload. Training scripts under `services/advisory-llm/train/` print
  dataset statistics (row counts, label distributions) — offline tooling, not the live
  request path, no applicant data. No `.env` file has ever been committed (checked git
  history); `.gitignore` excludes `.env`/`.env.*`.

## Known gaps — not addressed in this pass, and why

- **No authentication or authorization anywhere.** This is the largest gap. Every
  endpoint — including the Officer Dashboard's application list — is fully public, with
  no login, no API key, no role separation between an applicant and an officer. This
  matches `docs/api-contract.md`'s existing "Auth: none for this hackathon build"
  statement, so it's a known, previously-documented limitation, not a new discovery —
  but it's worth restating plainly here since it's the single biggest thing a real
  Ministry deployment would need before handling real citizen data.
- **No encryption at rest.** Postgres runs the stock `postgres:16-alpine` image with a
  plain Docker volume — no encrypted disk, no column-level encryption (e.g. `pgcrypto`)
  for the applicant data it stores (name, location, category, ESS score). Production
  would need at minimum an encrypted volume/disk at the infrastructure layer.
- **No TLS/HTTPS anywhere.** Every service, including the gateway, is plain HTTP —
  fine for a local/demo environment, not acceptable once this leaves a trusted network.
  Production needs TLS termination (e.g. at a reverse proxy or load balancer) in front
  of `backend-api` and the frontend.
- **No audit trail.** There's no record of who changed an application's `status`, no
  access log beyond uvicorn's default request line (method/path/status, not who).
  Meaningful audit logging needs real authentication first — an audit entry is only
  useful if it can name an actor, and today nothing can.
- **No data retention or deletion policy.** The `applications` table grows without a
  TTL or purge job, and there's no way for an applicant to request deletion of their
  data (no right-to-erasure mechanism).
- **Frontend-side CSP not set.** The `Content-Security-Policy` header added in this pass
  is on `backend-api`'s JSON responses, which has limited practical effect — CSP is
  primarily enforced based on the header sent with the HTML *document* itself, which is
  served by `frontend/nginx.conf` in docker-compose (or the Vite dev server locally),
  not by backend-api. Adding a document-level CSP is a small, clearly-scoped follow-up,
  left undone here because it touches frontend infrastructure and this pass was scoped
  to `backend-api/` + docs only.
- **Pydantic bounds not fully consistent across services** (found by reading each
  service's `app/schemas.py`, not fixed — out of this pass's scope): `services/
  calculator`'s `CalculatorRequest.location`/`.category` and `services/feasibility`'s
  equivalents have no `max_length`; `services/advisory-llm`'s `SchemeMatchRequest`
  accepts `gender`/`location_type` as unconstrained strings rather than the closed set
  the model actually expects, and several of its numeric fields (`years_operating`,
  `annual_family_income`, `monthly_revenue`, `requested_amount`, `margin_capital`) have
  a lower bound but no upper one. `services/advisory-llm/` is also currently off-limits
  for edits — a teammate has in-flight handoffs there — so this is a flagged follow-up
  for whoever owns that file next, not something silently left broken.
- **No rate limiting or request-size limits** on any endpoint. Not implemented,
  not assessed further here — flagging rather than guessing at a fix.

## DPDP Act 2023 — alignment statement

This prototype processes personal data (applicant name where provided, location,
business category, and financial figures like requested capital and revenue) and, via
the Scheme Match feature, category/gender data used for eligibility matching — data a
real deployment would need to treat as personal data under the Digital Personal Data
Protection Act, 2023, with `backend-api`/the project's operator as the Data Fiduciary
and applicants as Data Principals.

**What this prototype does NOT yet implement, honestly stated:**

- **No consent capture.** There's no notice-and-consent step at intake (DPDP Sections
  5–6) — the wizard simply collects the data needed for each calculation with no
  explanation of purpose or opt-in.
- **No Data Principal rights.** No way for an applicant to access, correct, or request
  erasure of their submitted data (Sections 11–13) beyond a developer manually querying
  Postgres.
- **No breach notification process** (Section 8(6)) — there's no mechanism to detect or
  report one in the first place, let alone notify the Data Protection Board or affected
  individuals.
- **No designated grievance/redress contact**, as the Act expects a Data Fiduciary to
  provide.
- **No data retention limit** tied to purpose, and no deletion workflow once the stated
  purpose is served.

**What a production path would need**, roughly in the order it'd need to happen: (1) a
real authentication/authorization layer, since data-subject-rights and consent tracking
are meaningless without knowing who's who; (2) an explicit consent notice at data
collection, in the applicant's chosen language, before any data is submitted; (3) a
retention policy with automated purge, and an erasure endpoint; (4) encryption at rest
and in transit (see above); (5) a designated grievance officer/contact and a documented
breach-response process; (6) a legal review of whether this system's scale/nature
triggers Significant Data Fiduciary obligations, which is a legal determination, not an
engineering one, and out of scope for this document.

None of the above is implemented today. Stating it here is the honest alternative to
either ignoring compliance entirely or claiming it's handled when it isn't.
