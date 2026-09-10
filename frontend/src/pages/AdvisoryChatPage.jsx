import { useState } from 'react'
import { sendAdvisoryChat } from '../api/advisoryChat.js'
import { useI18n } from '../i18n/I18nContext.jsx'

// Uses POST /api/advisory-chat (see docs/api-contract.md #4). This service has been live
// and working since it was first dockerized, but had no UI at all — the API client
// (api/advisoryChat.js) was imported nowhere. This is a minimal chat widget so it's
// actually reachable from the app, not just curl.
let conversationCounter = 0
function newConversationId() {
  conversationCounter += 1
  return `conv_${Date.now()}_${conversationCounter}`
}

export default function AdvisoryChatPage() {
  const { t } = useI18n()
  const [conversationId] = useState(newConversationId)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSend = (e) => {
    e.preventDefault()
    const text = draft.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setDraft('')
    setLoading(true)
    setError(null)

    sendAdvisoryChat({ message: text, context: { conversation_id: conversationId } })
      .then((result) => {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: result.response_text,
            citedSources: result.cited_sources,
            detectedLanguage: result.detected_language,
          },
        ])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{t('advisoryChat.title')}</h1>
        <p className="text-sm text-slate-500">{t('advisoryChat.subtitle')}</p>
      </div>

      <div className="flex min-h-[24rem] flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 && (
            <p className="text-sm text-slate-400">{t('advisoryChat.emptyState')}</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                  m.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-800'
                }`}
              >
                <p>{m.text}</p>
                {m.citedSources && m.citedSources.length > 0 && (
                  <ul className="mt-2 space-y-1 border-t border-slate-300/50 pt-2 text-xs opacity-90">
                    {m.citedSources.map((src, j) => (
                      <li key={j}>
                        {src.url ? (
                          <a href={src.url} target="_blank" rel="noreferrer" className="underline">
                            {src.scheme} — {src.document}
                          </a>
                        ) : (
                          <span>
                            {src.scheme} — {src.document}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
          {loading && <p className="text-sm text-slate-400">{t('common.loading')}</p>}
        </div>

        {error && (
          <p className="border-t border-slate-100 px-4 py-2 text-sm text-red-600">
            {t('common.errorGeneric')}
          </p>
        )}

        <form onSubmit={handleSend} className="flex gap-2 border-t border-slate-200 p-3">
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={t('advisoryChat.inputPlaceholder')}
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <button
            type="submit"
            disabled={loading || !draft.trim()}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-60"
          >
            {t('advisoryChat.sendCta')}
          </button>
        </form>
      </div>
    </div>
  )
}
