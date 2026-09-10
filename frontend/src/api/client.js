// Thin fetch wrapper for backend-api (the gateway, port 8000). Never call services/* directly
// — see docs/api-contract.md. All gateway routes are proxied under /api/* in dev (vite.config.js).

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false'

export function isMockMode() {
  return USE_MOCKS
}

async function handleResponse(res, path) {
  if (!res.ok) {
    const payload = await res.json().catch(() => null)
    const message = payload?.error?.message || `Request to ${path} failed with ${res.status}`
    const error = new Error(message)
    error.code = payload?.error?.code
    error.status = res.status
    throw error
  }

  return res.json()
}

export async function postJson(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  return handleResponse(res, path)
}

export async function getJson(path) {
  const res = await fetch(`/api${path}`)
  return handleResponse(res, path)
}

// Simulates network latency for mock responses so loading states are visible during dev.
export function mockDelay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
