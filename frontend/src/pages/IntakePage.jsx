import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useIntake } from '../context/IntakeContext.jsx'
import { useI18n } from '../i18n/I18nContext.jsx'

export default function IntakePage() {
  const { t } = useI18n()
  const { intake, setIntake, setFeasibility, setCalculator } = useIntake()
  const [form, setForm] = useState(intake)
  const navigate = useNavigate()

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setIntake({ ...form, margin_capital: Number(form.margin_capital) })
    // Invalidate downstream results so a changed intake always triggers a fresh fetch.
    setFeasibility(null)
    setCalculator(null)
    navigate('/feasibility')
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">{t('intake.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <label htmlFor="location" className="mb-1 block text-sm font-medium text-slate-700">
            {t('intake.locationLabel')}
          </label>
          <input
            id="location"
            type="text"
            required
            value={form.location}
            onChange={handleChange('location')}
            placeholder={t('intake.locationPlaceholder')}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <div>
          <label htmlFor="category" className="mb-1 block text-sm font-medium text-slate-700">
            {t('intake.categoryLabel')}
          </label>
          <input
            id="category"
            type="text"
            required
            value={form.category}
            onChange={handleChange('category')}
            placeholder={t('intake.categoryPlaceholder')}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <div>
          <label htmlFor="margin_capital" className="mb-1 block text-sm font-medium text-slate-700">
            {t('intake.marginCapitalLabel')}
          </label>
          <input
            id="margin_capital"
            type="number"
            min="0"
            required
            value={form.margin_capital}
            onChange={handleChange('margin_capital')}
            placeholder={t('intake.marginCapitalPlaceholder')}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <button
          type="submit"
          className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          {t('intake.submitCta')}
        </button>
      </form>
    </div>
  )
}
