import { useState } from 'react'
import { fetchSchemeMatch } from '../api/schemeMatch.js'
import { useIntake } from '../context/IntakeContext.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'

const EMPTY_PROFILE = {
  gender: 'female',
  is_sc_st: false,
  is_new_business: false,
  years_operating: '',
  location_type: 'rural',
  annual_family_income: '',
  monthly_revenue: '',
  requested_amount: '',
}

// Uses POST /api/scheme-match — a real, locally trained RandomForestClassifier
// (see services/advisory-llm/app/scheme_match.py), not a rules lookup and not
// an external API call. `category` and `margin_capital` come from the wizard's
// intake step; this page only collects the extra fields the classifier needs.
export default function SchemeMatchPage() {
  const { t } = useI18n()
  const { intake } = useIntake()
  const [profile, setProfile] = useState(EMPTY_PROFILE)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    fetchSchemeMatch({
      category: intake.category,
      is_new_business: profile.is_new_business,
      years_operating: Number(profile.years_operating) || 0,
      gender: profile.gender,
      is_sc_st: profile.is_sc_st,
      location_type: profile.location_type,
      annual_family_income: Number(profile.annual_family_income) || 0,
      monthly_revenue: Number(profile.monthly_revenue) || 0,
      requested_amount: Number(profile.requested_amount) || 1,
      margin_capital: Number(intake.margin_capital) || 0,
    })
      .then(setResult)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  if (!result) {
    return (
      <div className="space-y-6">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-800">
            {t('schemeMatch.modelBadge')}
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">{t('schemeMatch.title')}</h1>
          <p className="mt-1 text-sm text-slate-500">{t('schemeMatch.intro')}</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label htmlFor="gender" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.genderLabel')}
              </label>
              <select
                id="gender"
                value={profile.gender}
                onChange={handleChange('gender')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="female">{t('schemeMatch.genderFemale')}</option>
                <option value="male">{t('schemeMatch.genderMale')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="location_type" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.locationTypeLabel')}
              </label>
              <select
                id="location_type"
                value={profile.location_type}
                onChange={handleChange('location_type')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="rural">{t('schemeMatch.locationTypeRural')}</option>
                <option value="semi-urban">{t('schemeMatch.locationTypeSemiUrban')}</option>
                <option value="urban">{t('schemeMatch.locationTypeUrban')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="years_operating" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.yearsOperatingLabel')}
              </label>
              <input
                id="years_operating"
                type="number"
                min="0"
                step="0.5"
                value={profile.years_operating}
                onChange={handleChange('years_operating')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label htmlFor="requested_amount" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.requestedAmountLabel')}
              </label>
              <input
                id="requested_amount"
                type="number"
                min="1"
                required
                value={profile.requested_amount}
                onChange={handleChange('requested_amount')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label htmlFor="annual_family_income" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.annualFamilyIncomeLabel')}
              </label>
              <input
                id="annual_family_income"
                type="number"
                min="0"
                value={profile.annual_family_income}
                onChange={handleChange('annual_family_income')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label htmlFor="monthly_revenue" className="mb-1 block text-sm font-medium text-slate-700">
                {t('schemeMatch.monthlyRevenueLabel')}
              </label>
              <input
                id="monthly_revenue"
                type="number"
                min="0"
                value={profile.monthly_revenue}
                onChange={handleChange('monthly_revenue')}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={profile.is_sc_st}
                onChange={handleChange('is_sc_st')}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              {t('schemeMatch.isScStLabel')}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={profile.is_new_business}
                onChange={handleChange('is_new_business')}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              {t('schemeMatch.isNewBusinessLabel')}
            </label>
          </div>

          {error && <p className="text-sm text-red-600">{t('common.errorGeneric')}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {loading ? t('common.loading') : t('schemeMatch.submitCta')}
          </button>
        </form>
      </div>
    )
  }

  const { results, model_feature_importance: importance } = result
  const topImportance = Object.entries(importance || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-800">
          {t('schemeMatch.modelBadge')}
        </div>
        <h1 className="text-2xl font-semibold text-slate-900">{t('schemeMatch.resultsTitle')}</h1>
      </div>

      <div className="space-y-4">
        {results.map((r, i) => (
          <section
            key={r.scheme}
            className={`rounded-lg border p-6 shadow-sm ${
              i === 0 ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <a
                href={r.url}
                target="_blank"
                rel="noreferrer"
                className="text-lg font-semibold text-slate-900 hover:underline"
              >
                {r.display_name}
              </a>
              <span className="text-sm font-medium text-indigo-700">
                {(r.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-indigo-500"
                style={{ width: `${Math.max(r.confidence * 100, 2)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-500">{t('schemeMatch.confidenceLabel')}</p>

            <div className="mt-4">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t('schemeMatch.whyLabel')}
              </p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {r.why.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          </section>
        ))}
      </div>

      {topImportance.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            {t('schemeMatch.featureImportanceTitle')}
          </h2>
          <ul className="space-y-2 text-sm">
            {topImportance.map(([feature, weight]) => (
              <li key={feature} className="flex items-center gap-3">
                <span className="w-40 shrink-0 text-slate-600">{feature}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-slate-400"
                    style={{ width: `${weight * 100}%` }}
                  />
                </div>
                <span className="w-12 text-right text-xs text-slate-500">
                  {(weight * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-xs text-slate-500">{t('schemeMatch.disclaimer')}</p>

      <button
        onClick={() => setResult(null)}
        className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        {t('schemeMatch.recalculate')}
      </button>
    </div>
  )
}
