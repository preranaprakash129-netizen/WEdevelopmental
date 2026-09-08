// Thin fetch wrapper for backend-api (the gateway, port 8000). Never call services/* directly
// — see docs/api-contract.md. All gateway routes are proxied under /api/* in dev (vite.config.js).

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false'

export function isMockMode() {
  return USE_MOCKS
}

export async function postJson(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

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

// Simulates network latency for mock responses so loading states are visible during dev.
export function mockDelay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
