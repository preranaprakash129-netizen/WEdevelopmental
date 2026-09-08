import { useI18n } from '../i18n/I18nContext.jsx'

// Placeholder officer view. There is no list/aggregate endpoint in docs/api-contract.md yet
// (contract only covers single-applicant feasibility/calculator/ess-score/advisory-chat) —
// this fills in with static rows shaped like what an ess-score-driven table would show, and
// should be wired up once backend-api exposes an applicants list.
const PLACEHOLDER_ROWS = [
  { applicant: 'Meena Kumari', category: 'dairy', location: 'Rampur', ess_score: 61.0, status: 'Under review' },
  { applicant: 'Arun Singh', category: 'tailoring', location: 'Sitapur', ess_score: 74.2, status: 'Approved' },
]

export default function DashboardPage() {
  const { t } = useI18n()

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{t('dashboard.title')}</h1>
        <p className="text-sm text-slate-500">{t('dashboard.subtitle')}</p>
      </div>

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
            {PLACEHOLDER_ROWS.map((row) => (
              <tr key={row.applicant} className="border-b border-slate-100">
                <td className="px-4 py-2 text-slate-800">{row.applicant}</td>
                <td className="px-4 py-2 text-slate-600">{row.category}</td>
                <td className="px-4 py-2 text-slate-600">{row.location}</td>
                <td className="px-4 py-2 text-slate-600">{row.ess_score}</td>
                <td className="px-4 py-2 text-slate-600">{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400">{t('dashboard.placeholder')}</p>
    </div>
  )
}
