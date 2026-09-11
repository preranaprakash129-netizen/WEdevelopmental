import { Link, useLocation } from 'react-router-dom'
import { useI18n } from '../i18n/I18nContext.jsx'

// Reached via the "Save Application Summary" button on the Scheme Match results view
// (SchemeMatchPage.jsx), which passes everything needed as router navigation state --
// nothing is persisted or re-fetched here. Router state doesn't survive a page reload,
// so a direct visit/reload with no state shows a friendly fallback rather than crashing.
export default function ApplicationSummaryPage() {
  const { t } = useI18n()
  const location = useLocation()
  const data = location.state

  if (!data || !data.topResult) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-slate-900">{t('applicationSummary.title')}</h1>
        <p className="text-sm text-slate-600">{t('applicationSummary.noData')}</p>
        <Link to="/scheme-match" className="text-sm font-medium text-indigo-700 hover:underline">
          {t('applicationSummary.backToSchemeMatch')} →
        </Link>
      </div>
    )
  }

  const { intake, profile, topResult, essScore } = data

  return (
    <div className="space-y-6 print:space-y-4">
      <div className="flex items-center justify-between print:hidden">
        <h1 className="text-2xl font-semibold text-slate-900">{t('applicationSummary.title')}</h1>
        <div className="flex gap-2">
          <button
            onClick={() => window.print()}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {t('applicationSummary.printCta')}
          </button>
          <Link
            to="/scheme-match"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {t('applicationSummary.backToSchemeMatch')}
          </Link>
        </div>
      </div>

      <div className="hidden print:block">
        <h1 className="text-xl font-bold text-slate-900">{t('applicationSummary.title')}</h1>
        <p className="text-xs text-slate-500">{new Date().toLocaleDateString()}</p>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm print:border-0 print:p-0 print:shadow-none">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          {t('applicationSummary.profileTitle')}
        </h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-slate-500">{t('intake.locationLabel')}</dt>
            <dd className="font-medium text-slate-900">{intake?.location || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('intake.categoryLabel')}</dt>
            <dd className="font-medium text-slate-900">{intake?.category || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('intake.marginCapitalLabel')}</dt>
            <dd className="font-medium text-slate-900">{intake?.margin_capital || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.genderLabel')}</dt>
            <dd className="font-medium text-slate-900">
              {profile?.gender === 'female' ? t('schemeMatch.genderFemale') : t('schemeMatch.genderMale')}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.locationTypeLabel')}</dt>
            <dd className="font-medium text-slate-900">{profile?.location_type || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.yearsOperatingLabel')}</dt>
            <dd className="font-medium text-slate-900">{profile?.years_operating || '0'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.requestedAmountLabel')}</dt>
            <dd className="font-medium text-slate-900">{profile?.requested_amount || '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.isScStLabel')}</dt>
            <dd className="font-medium text-slate-900">
              {profile?.is_sc_st ? t('applicationSummary.yes') : t('applicationSummary.no')}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('schemeMatch.isNewBusinessLabel')}</dt>
            <dd className="font-medium text-slate-900">
              {profile?.is_new_business ? t('applicationSummary.yes') : t('applicationSummary.no')}
            </dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm print:border-0 print:bg-white print:p-0 print:shadow-none">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-indigo-700">
          {t('applicationSummary.topSchemeTitle')}
        </h2>
        <p className="text-lg font-semibold text-slate-900">{topResult.display_name}</p>
        <p className="text-sm text-indigo-700">
          {t('schemeMatch.confidenceLabel')}: {(topResult.confidence * 100).toFixed(1)}%
        </p>
        {topResult.why && topResult.why.length > 0 && (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {topResult.why.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}

        {topResult.documents && topResult.documents.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
              {t('schemeMatch.documentsNeededTitle')}
            </p>
            <ul className="mt-1 flex flex-wrap gap-2 print:gap-1">
              {topResult.documents.map((doc) => (
                <li
                  key={doc}
                  className="rounded-full bg-white px-3 py-1 text-xs text-slate-700 print:rounded-none print:border print:border-slate-300"
                >
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        )}

        {topResult.apply_process && (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
              {t('schemeMatch.applyProcessTitle')}
            </p>
            <p className="mt-1 text-sm text-slate-700">{topResult.apply_process}</p>
          </div>
        )}

        <p className="mt-3 text-xs text-slate-500">
          <a href={topResult.url} target="_blank" rel="noreferrer" className="text-indigo-700 hover:underline">
            {topResult.url}
          </a>
        </p>
      </section>

      {essScore && (
        <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 shadow-sm print:border-0 print:bg-white print:p-0 print:shadow-none">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-emerald-700">
            {t('essScore.overallScore')}
          </h2>
          <p className="text-2xl font-bold text-emerald-700">{essScore.ess_score}</p>
        </section>
      )}

      <p className="text-xs text-slate-500 print:mt-6">{t('applicationSummary.disclaimer')}</p>
    </div>
  )
}
