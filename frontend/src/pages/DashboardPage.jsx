import { useEffect, useState } from 'react'
import { fetchApplications } from '../api/applications.js'
import { useI18n } from '../i18n/I18nContext.jsx'

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

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{t('dashboard.title')}</h1>
        <p className="text-sm text-slate-500">{t('dashboard.subtitle')}</p>
      </div>

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
