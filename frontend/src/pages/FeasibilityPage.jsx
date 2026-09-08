import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchFeasibility } from '../api/feasibility.js'
import { useIntake } from '../context/IntakeContext.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'

export default function FeasibilityPage() {
  const { t } = useI18n()
  const { intake, feasibility, setFeasibility } = useIntake()
  const [loading, setLoading] = useState(!feasibility)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (feasibility) return
    let cancelled = false
    setLoading(true)
    fetchFeasibility(intake)
      .then((data) => {
        if (!cancelled) setFeasibility(data)
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
    // Only fetch once per intake; re-running the intake form clears `feasibility` upstream.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) return <p className="text-slate-600">{t('common.loading')}</p>
  if (error) return <p className="text-red-600">{t('common.errorGeneric')}</p>
  if (!feasibility) return null

  const { market_reach, competitor_list, swot, pricing_bands, feasibility_score, confidence_range } = feasibility

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">{t('feasibility.title')}</h1>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-baseline gap-3">
          <span className="text-sm font-medium text-slate-500">{t('feasibility.feasibilityScore')}</span>
          <span className="text-3xl font-bold text-emerald-600">{feasibility_score}</span>
          <span className="text-sm text-slate-500">
            ({t('feasibility.confidenceRange')}: {confidence_range.low}&ndash;{confidence_range.high})
          </span>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('feasibility.marketReach')}</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-slate-500">{t('feasibility.estimatedCustomers')}</dt>
            <dd className="text-lg font-medium text-slate-900">{market_reach.estimated_customers}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('feasibility.radius')}</dt>
            <dd className="text-lg font-medium text-slate-900">{market_reach.radius_km}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('feasibility.competitors')}</h2>
        {competitor_list.length === 0 ? (
          <p className="text-sm text-slate-500">{t('feasibility.noCompetitors')}</p>
        ) : (
          <ul className="divide-y divide-slate-100 text-sm">
            {competitor_list.map((c) => (
              <li key={c.name} className="flex justify-between py-2">
                <span className="text-slate-800">{c.name}</span>
                <span className="text-slate-500">{c.category}</span>
                <span className="text-slate-500">{c.distance_km} km</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('feasibility.swot')}</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[
            ['strengths', swot.strengths],
            ['weaknesses', swot.weaknesses],
            ['opportunities', swot.opportunities],
            ['threats', swot.threats],
          ].map(([key, items]) => (
            <div key={key}>
              <h3 className="mb-1 text-sm font-semibold text-slate-700">{t(`feasibility.${key}`)}</h3>
              <ul className="list-inside list-disc text-sm text-slate-600">
                {items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('feasibility.pricingBands')}</h2>
        <dl className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <dt className="text-slate-500">{t('feasibility.low')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{pricing_bands.low}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('feasibility.median')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{pricing_bands.median}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('feasibility.high')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{pricing_bands.high}</dd>
          </div>
        </dl>
      </section>

      <button
        onClick={() => navigate('/calculator')}
        className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        {t('feasibility.continueCta')}
      </button>
    </div>
  )
}
