// Plain SVG radar chart, no charting library dependency (no npm install needed
// to use it). Renders the 4 deterministic, rule-based sub-scores behind a
// scheme's confidence number -- see services/advisory-llm/app/scheme_match.py's
// _match_breakdown for exactly how each axis is computed. This is real model
// output translated into a picture, not decoration: every value plotted here
// traces back to a verifiable rule over scheme_facts.py, the same way the
// "why" bullets do.
const AXES = [
  { key: 'category_fit', angle: -90 },
  { key: 'loan_amount_fit', angle: 0 },
  { key: 'eligibility_fit', angle: 90 },
  { key: 'priority_boost_fit', angle: 180 },
]

const SIZE = 160
const CENTER = SIZE / 2
const RADIUS = SIZE / 2 - 28

function pointOnAxis(angleDeg, value) {
  const rad = (angleDeg * Math.PI) / 180
  const r = RADIUS * Math.max(0, Math.min(1, value))
  return [CENTER + r * Math.cos(rad), CENTER + r * Math.sin(rad)]
}

function labelPoint(angleDeg, offset = 18) {
  const rad = (angleDeg * Math.PI) / 180
  return [CENTER + (RADIUS + offset) * Math.cos(rad), CENTER + (RADIUS + offset) * Math.sin(rad)]
}

// breakdown: { category_fit, loan_amount_fit, eligibility_fit, priority_boost_fit }
// labels: { category_fit, loan_amount_fit, eligibility_fit, priority_boost_fit } (translated axis names)
export default function MatchRadarChart({ breakdown, labels }) {
  if (!breakdown) return null

  const polygonPoints = AXES.map((axis) => pointOnAxis(axis.angle, breakdown[axis.key] ?? 0))
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
    .join(' ')

  const ringLevels = [0.25, 0.5, 0.75, 1.0]

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE} role="img" aria-label="Match breakdown radar chart">
      {/* Background rings */}
      {ringLevels.map((level) => (
        <polygon
          key={level}
          points={AXES.map((axis) => pointOnAxis(axis.angle, level))
            .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
            .join(' ')}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="1"
        />
      ))}
      {/* Axis lines */}
      {AXES.map((axis) => {
        const [x, y] = pointOnAxis(axis.angle, 1.0)
        return <line key={axis.key} x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="#e2e8f0" strokeWidth="1" />
      })}
      {/* Data polygon */}
      <polygon points={polygonPoints} fill="rgba(79, 70, 229, 0.25)" stroke="#4f46e5" strokeWidth="2" />
      {/* Data points */}
      {AXES.map((axis) => {
        const [x, y] = pointOnAxis(axis.angle, breakdown[axis.key] ?? 0)
        return <circle key={axis.key} cx={x} cy={y} r="3" fill="#4f46e5" />
      })}
      {/* Axis labels */}
      {AXES.map((axis) => {
        const [x, y] = labelPoint(axis.angle)
        return (
          <text
            key={axis.key}
            x={x}
            y={y}
            fontSize="8"
            fill="#475569"
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {labels?.[axis.key] ?? axis.key}
          </text>
        )
      })}
    </svg>
  )
}
