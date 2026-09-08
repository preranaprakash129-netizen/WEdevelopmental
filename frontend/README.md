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
