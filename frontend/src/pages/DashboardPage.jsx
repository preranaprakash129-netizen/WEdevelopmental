import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchApplicationInsights, fetchApplications } from '../api/applications.js'
import { useI18n } from '../i18n/I18nContext.jsx'

// Plain inline SVG, no charting library — same reasoning as MatchRadarChart.jsx on
// the Scheme Match page (no npm install needed to use it). Renders the real
// ess_score_histogram.buckets from GET /api/applications/insights.
function EssHistogramChart({ buckets }) {
  const width = 260
  const height = 100
  const gap = 6
  const barWidth = (width - gap * (buckets.length - 1)) / buckets.length
  const maxCount = Math.max(1, ...buckets.map((b) => b.count))

  return (
    <svg viewBox={`0 0 ${width} ${height + 16}`} width={width} height={height + 16} role="img" aria-label="ESS score distribution">
      {buckets.map((bucket, i) => {
        const barHeight = (bucket.count / maxCount) * height
        const x = i * (barWidth + gap)
        const y = height - barHeight
        return (
          <g key={bucket.range}>
            <rect x={x} y={y} width={barWidth} height={Math.max(barHeight, bucket.count > 0 ? 2 : 0)} fill="#4f46e5" rx="2" />
            <text x={x + barWidth / 2} y={height + 12} fontSize="9" fill="#475569" textAnchor="middle">
              {bucket.range}
            </text>
            {bucket.count > 0 && (
              <text x={x + barWidth / 2} y={y - 3} fontSize="9" fill="#334155" textAnchor="middle">
                {bucket.count}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

// Uses GET /api/applications (see docs/api-contract.md #5). Each row is a real wizard run
// recorded from EssScorePage — either with a real ESS score, or null if the applicant
// skipped that step. Previously this page was two hardcoded placeholder rows; there's still
// no applicant-name field in the wizard's Intake step, so that column falls back to
// category+location when no name is on record.
export default function DashboardPage() {
  const { t } = useI18n()
  const [applications, setApplications] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetched independently from the applications list — a slow/failed insights call
  // should never block the applicant table from rendering, and vice versa.
  const [insights, setInsights] = useState(null)
  const [insightsError, setInsightsError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchApplications()
      .then((data) => {
        if (!cancelled) setApplications(data.applications)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    fetchApplicationInsights()
      .then((data) => {
        if (!cancelled) setInsights(data)
      })
      .catch((err) => {
        if (!cancelled) setInsightsError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{t('dashboard.title')}</h1>
        <p className="text-sm text-slate-500">{t('dashboard.subtitle')}</p>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-indigo-900">{t('dashboard.aiBannerText')}</p>
        <Link
          to="/scheme-match"
          className="inline-flex shrink-0 items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {t('dashboard.aiBannerCta')}
        </Link>
      </div>

      {insightsError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {t('dashboard.loadError')}
        </div>
      )}

      {insights && insights.total_applications > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t('dashboard.insightsTitle')}
          </h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-medium text-slate-600">{t('dashboard.insightsCategoryTitle')}</p>
              <ul className="space-y-2 text-sm">
                {insights.category_breakdown.map(({ category, count }) => {
                  const maxCount = Math.max(...insights.category_breakdown.map((c) => c.count))
                  return (
                    <li key={category} className="flex items-center gap-3">
                      <span className="w-28 shrink-0 truncate text-slate-600">{category}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-indigo-500"
                          style={{ width: `${Math.max((count / maxCount) * 100, 4)}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-xs text-slate-500">{count}</span>
                    </li>
                  )
                })}
              </ul>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-slate-600">{t('dashboard.insightsEssHistogramTitle')}</p>
              <EssHistogramChart buckets={insights.ess_score_histogram.buckets} />
              {insights.ess_score_histogram.unscored_count > 0 && (
                <p className="mt-1 text-xs text-slate-500">
                  {insights.ess_score_histogram.unscored_count} {t('dashboard.insightsUnscoredSuffix')}
                </p>
              )}
            </div>
          </div>

          <p className="mt-4 border-t border-slate-200 pt-3 text-xs text-slate-500">
            {t('dashboard.insightsSchemeGapNote')}
          </p>
        </section>
      )}

      {loading && <p className="text-slate-600">{t('common.loading')}</p>}

      {error && !loading && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {t('dashboard.loadError')}
        </div>
      )}

      {!loading && !error && applications && applications.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
          {t('dashboard.empty')}
        </div>
      )}

      {!loading && !error && applications && applications.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-slate-500">
                <th className="px-4 py-2">{t('dashboard.columnApplicant')}</th>
                <th className="px-4 py-2">{t('dashboard.columnCategory')}</th>
                <th className="px-4 py-2">{t('dashboard.columnLocation')}</th>
                <th className="px-4 py-2">{t('dashboard.columnEssScore')}</th>
                <th className="px-4 py-2">{t('dashboard.columnStatus')}</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((row) => (
                <tr key={row.id} className="border-b border-slate-100">
                  <td className="px-4 py-2 text-slate-800">
                    {row.applicant_name || `${row.category} — ${row.location}`}
                  </td>
                  <td className="px-4 py-2 text-slate-600">{row.category}</td>
                  <td className="px-4 py-2 text-slate-600">{row.location}</td>
                  <td className="px-4 py-2 text-slate-600">
                    {row.ess_score !== null && row.ess_score !== undefined
                      ? row.ess_score
                      : t('dashboard.essScoreSkipped')}
                  </td>
                  <td className="px-4 py-2 text-slate-600">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
