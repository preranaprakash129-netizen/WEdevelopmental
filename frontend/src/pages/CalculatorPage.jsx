import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCalculator } from '../api/calculator.js'
import { useIntake } from '../context/IntakeContext.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'

export default function CalculatorPage() {
  const { t } = useI18n()
  const { intake, calculator, setCalculator } = useIntake()
  const [requestedLoan, setRequestedLoan] = useState('')
  const [loading, setLoading] = useState(!calculator)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const runCalculation = (loanOverride) => {
    setLoading(true)
    setError(null)
    fetchCalculator({
      margin_capital: intake.margin_capital,
      category: intake.category,
      location: intake.location,
      requested_loan_amount: loanOverride ? Number(loanOverride) : undefined,
    })
      .then(setCalculator)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (calculator) return
    runCalculation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) return <p className="text-slate-600">{t('common.loading')}</p>
  if (error) return <p className="text-red-600">{t('common.errorGeneric')}</p>
  if (!calculator) return null

  const { project_cost, scheme_selected, loan_amount, emi_schedule, moratorium, working_capital } = calculator

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">{t('calculator.title')}</h1>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1">
            <label htmlFor="requested_loan" className="mb-1 block text-sm font-medium text-slate-700">
              {t('calculator.requestedLoanLabel')}
            </label>
            <input
              id="requested_loan"
              type="number"
              min="0"
              value={requestedLoan}
              onChange={(e) => setRequestedLoan(e.target.value)}
              placeholder={t('calculator.requestedLoanPlaceholder')}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <button
            onClick={() => runCalculation(requestedLoan)}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900"
          >
            {t('calculator.recalculate')}
          </button>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-slate-500">{t('calculator.projectCost')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{project_cost.toLocaleString('en-IN')}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('calculator.schemeSelected')}</dt>
            <dd className="text-lg font-medium text-slate-900">
              {scheme_selected.name} ({scheme_selected.subsidy_percent}% {t('calculator.subsidyPercent')})
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('calculator.loanAmount')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{loan_amount.toLocaleString('en-IN')}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{t('calculator.workingCapital')}</dt>
            <dd className="text-lg font-medium text-slate-900">₹{working_capital.toLocaleString('en-IN')}</dd>
          </div>
        </dl>
        {moratorium.months > 0 && (
          <p className="mt-4 text-sm text-slate-600">
            {t('calculator.moratorium')}: {moratorium.months} {t('calculator.moratoriumMonths')}
            {moratorium.reason ? ` — ${moratorium.reason}` : ''}
          </p>
        )}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">{t('calculator.emiSchedule')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-2 pr-4">{t('calculator.month')}</th>
                <th className="py-2 pr-4">{t('calculator.emi')}</th>
                <th className="py-2 pr-4">{t('calculator.principal')}</th>
                <th className="py-2 pr-4">{t('calculator.interest')}</th>
                <th className="py-2 pr-4">{t('calculator.balance')}</th>
              </tr>
            </thead>
            <tbody>
              {emi_schedule.map((row) => (
                <tr key={row.month} className="border-b border-slate-100">
                  <td className="py-2 pr-4">{row.month}</td>
                  <td className="py-2 pr-4">₹{row.emi.toLocaleString('en-IN')}</td>
                  <td className="py-2 pr-4">₹{row.principal_component.toLocaleString('en-IN')}</td>
                  <td className="py-2 pr-4">₹{row.interest_component.toLocaleString('en-IN')}</td>
                  <td className="py-2 pr-4">₹{row.outstanding_balance.toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <button
        onClick={() => navigate('/dashboard')}
        className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        {t('calculator.continueCta')}
      </button>
    </div>
  )
}
