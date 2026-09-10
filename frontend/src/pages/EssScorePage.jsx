import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitApplication } from '../api/applications.js'
import { fetchEssScore } from '../api/essScore.js'
import { useIntake } from '../context/IntakeContext.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'

// Records this wizard run on the officer dashboard (see docs/api-contract.md #5). Best-effort:
// a submission failure here (e.g. DB not up yet) must never block the applicant from
// continuing, so callers swallow the error rather than surfacing it.
function recordApplication(intake, essScoreResult) {
  submitApplication({
    location: intake.location,
    category: intake.category,
    ess_score: essScoreResult?.ess_score,
  }).catch(() => {
    // Dashboard just won't show this run; not worth interrupting the applicant's flow.
  })
}

const EMPTY_PROFILE = {
  years_operating: '',
  monthly_revenue: '',
  employee_count: '',
  has_bank_account: true,
}

// Uses POST /api/ess-score with profile_data (see docs/api-contract.md #3). This step is
// framed as optional: the wizard's three required inputs (location/category/margin_capital)
// don't include the operating-history fields ess-scoring needs, so we collect them here with
// their own small form rather than bloating the Intake step for every applicant.
export default function EssScorePage() {
  const { t } = useI18n()
  const { intake, essScore, setEssScore } = useIntake()
  const [profile, setProfile] = useState(EMPTY_PROFILE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleChange = (field) => (e) => {
    const value = field === 'has_bank_account' ? e.target.checked : e.target.value
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    fetchEssScore({
      profile_data: {
        category: intake.category,
        years_operating: Number(profile.years_operating),
        monthly_revenue: Number(profile.monthly_revenue),
        employee_count: profile.employee_count ? Number(profile.employee_count) : undefined,
        has_bank_account: profile.has_bank_account,
      },
    })
      .then((result) => {
        setEssScore(result)
        recordApplication(intake, result)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  if (!essScore) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-slate-900">{t('essScore.title')}</h1>
        <p className="text-sm text-slate-500">{t('essScore.intro')}</p>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div>
            <label htmlFor="years_operating" className="mb-1 block text-sm font-medium text-slate-700">
              {t('essScore.yearsOperatingLabel')}
            </label>
            <input
              id="years_operating"
              type="number"
              min="0"
              step="0.5"
              required
              value={profile.years_operating}
              onChange={handleChange('years_operating')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label htmlFor="monthly_revenue" className="mb-1 block text-sm font-medium text-slate-700">
              {t('essScore.monthlyRevenueLabel')}
            </label>
            <input
              id="monthly_revenue"
              type="number"
              min="0"
              required
              value={profile.monthly_revenue}
              onChange={handleChange('monthly_revenue')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label htmlFor="employee_count" className="mb-1 block text-sm font-medium text-slate-700">
              {t('essScore.employeeCountLabel')}
            </label>
            <input
              id="employee_count"
              type="number"
              min="0"
              value={profile.employee_count}
              onChange={handleChange('employee_count')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={profile.has_bank_account}
              onChange={handleChange('has_bank_account')}
              className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
            />
            {t('essScore.hasBankAccountLabel')}
          </label>

          {error && <p className="text-sm text-red-600">{t('common.errorGeneric')}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {loading ? t('common.loading') : t('essScore.submitCta')}
          </button>
        </form>

        <button
          onClick={() => {
            recordApplication(intake, null)
            navigate('/dashboard')
          }}
          className="text-sm font-medium text-slate-500 hover:text-slate-700"
        >
          {t('essScore.skipCta')}
        </button>
      </div>
    )
  }

  const { ess_score, sub_scores, attribution, top_improvement_action } = essScore
  const sortedAttribution = [...attribution].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">{t('essScore.title')}</h1>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-baseline gap-3">
          <span className="text-sm font-medium text-slate-500">{t('essScore.overallScore')}</span>
          <span className="text-3xl font-bold text-emerald-600">{ess_score}</span>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('essScore.subScores')}</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-slate-500">{t('essScore.financialHealth')}</dt>
            <dd className="text-lg font-medium text-slate-900">{sub_scores.financial_health}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('essScore.marketStability')}</dt>
            <dd className="text-lg font-medium text-slate-900">{sub_scores.market_stability}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('essScore.operationalMaturity')}</dt>
            <dd className="text-lg font-medium text-slate-900">{sub_scores.operational_maturity}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('essScore.growthPotential')}</dt>
            <dd className="text-lg font-medium text-slate-900">{sub_scores.growth_potential}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('essScore.attribution')}</h2>
        <ul className="divide-y divide-slate-100 text-sm">
          {sortedAttribution.map((a) => (
            <li key={a.feature} className="flex items-center justify-between py-2">
              <span className="text-slate-800">{a.feature}</span>
              <span className={a.impact >= 0 ? 'font-medium text-emerald-600' : 'font-medium text-red-600'}>
                {a.impact >= 0 ? '+' : ''}
                {a.impact}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-semibold text-emerald-900">{t('essScore.topImprovement')}</h2>
        <p className="text-sm text-emerald-800">{top_improvement_action.action}</p>
        <p className="mt-1 text-xs text-emerald-700">
          {t('essScore.expectedDelta')}: +{top_improvement_action.expected_score_delta}
        </p>
      </section>

      <button
        onClick={() => navigate('/dashboard')}
        className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        {t('essScore.continueCta')}
      </button>
    </div>
  )
}
