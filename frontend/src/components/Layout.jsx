import { NavLink, Outlet } from 'react-router-dom'
import { useI18n } from '../i18n/I18nContext.jsx'
import LanguageSwitcher from './LanguageSwitcher.jsx'

const navLinkClass = ({ isActive }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
  }`

export default function Layout() {
  const { t } = useI18n()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="text-lg font-semibold text-slate-900">{t('common.appName')}</span>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              {t('nav.intake')}
            </NavLink>
            <NavLink to="/feasibility" className={navLinkClass}>
              {t('nav.feasibility')}
            </NavLink>
            <NavLink to="/calculator" className={navLinkClass}>
              {t('nav.calculator')}
            </NavLink>
            <NavLink to="/dashboard" className={navLinkClass}>
              {t('nav.dashboard')}
            </NavLink>
          </nav>
          <LanguageSwitcher />
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
