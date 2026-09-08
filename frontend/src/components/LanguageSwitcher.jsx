import { useI18n } from '../i18n/I18nContext.jsx'

export default function LanguageSwitcher() {
  const { language, setLanguage, locales, t } = useI18n()

  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      <span className="sr-only">{t('common.languageLabel')}</span>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
      >
        {Object.entries(locales).map(([code, { label }]) => (
          <option key={code} value={code}>
            {label}
          </option>
        ))}
      </select>
    </label>
  )
}
