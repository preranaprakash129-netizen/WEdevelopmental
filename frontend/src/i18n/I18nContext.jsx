import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import en from './locales/en.json'
import hi from './locales/hi.json'

// Add new languages here as they're populated. Only English is filled in for now;
// missing keys in any other locale fall back to English so the UI never shows raw keys.
export const LOCALES = {
  en: { label: 'English', messages: en },
  hi: { label: 'हिन्दी', messages: hi },
}

const STORAGE_KEY = 'sih26091.language'

const I18nContext = createContext(null)

function resolveKey(messages, key) {
  return key.split('.').reduce((acc, part) => (acc && typeof acc === 'object' ? acc[part] : undefined), messages)
}

export function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'en'
    } catch {
      return 'en'
    }
  })

  const setLanguage = useCallback((lang) => {
    setLanguageState(lang)
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      // ignore storage errors (e.g. private browsing)
    }
  }, [])

  const t = useCallback(
    (key) => {
      const active = LOCALES[language]?.messages
      const value = active && resolveKey(active, key)
      if (value !== undefined) return value
      const fallback = resolveKey(en, key)
      return fallback !== undefined ? fallback : key
    },
    [language],
  )

  const value = useMemo(
    () => ({ language, setLanguage, t, locales: LOCALES }),
    [language, setLanguage, t],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used within I18nProvider')
  return ctx
}
