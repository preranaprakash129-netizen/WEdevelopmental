import { Navigate } from 'react-router-dom'

// Guards a wizard step so it can't be reached out of order (intake -> feasibility -> calculator).
// `ok` is the condition that must be true to render children; otherwise redirect to `fallback`.
export default function RequireStep({ ok, fallback, children }) {
  if (!ok) return <Navigate to={fallback} replace />
  return children
}
