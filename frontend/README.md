# frontend

Owner: person 5

React + Tailwind UI. Consumes `backend-api` (gateway) — do not call the four `services/*`
directly from the frontend, always go through `backend-api`.

See [`docs/api-contract.md`](../docs/api-contract.md) for request/response shapes.

## Local dev

```bash
npm install
npm run dev   # http://localhost:5173
```

The dev server proxies `/api/*` to `backend-api` at `http://localhost:8000` (see
`vite.config.js`).

## Mock mode

By default (`VITE_USE_MOCKS=true`), all API calls in `src/api/*` return contract-shaped
mock data instead of hitting the network — this lets every screen be built and demoed
before `backend-api` is up. Copy `.env.example` to `.env.local` and set
`VITE_USE_MOCKS=false` once you want real requests against the gateway.

## Structure

- `src/pages/` — one component per route: intake, feasibility report, calculator, officer
  dashboard.
- `src/api/` — one client module per contract endpoint (`feasibility.js`, `calculator.js`,
  `essScore.js`, `advisoryChat.js`), each with a mock fallback matching
  `docs/api-contract.md` exactly.
- `src/context/IntakeContext.jsx` — carries intake form data + feasibility/calculator
  results between wizard steps (backed by `sessionStorage`, cleared on tab close).
- `src/i18n/` — language switcher scaffolding. `locales/en.json` is fully populated;
  other locale files (e.g. `hi.json`) start empty and fall back to English key-by-key, so
  adding a language is just filling in keys, not restructuring components.

## Page flow

Intake → Feasibility Report → Calculator is a linear wizard: each step redirects back to
the previous one if its prerequisite data isn't in context yet (see
`src/components/RequireStep.jsx`). The officer dashboard (`/dashboard`) is a separate view
reachable at any time.
