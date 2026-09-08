import { isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #4 POST /advisory-chat
const MOCK_RESPONSE = {
  response_text:
    'PMEGP ke liye aap apne zile ke KVIC/DIC office mein online apply kar sakte hain...',
  cited_sources: [
    { scheme: 'PMEGP', document: 'PMEGP Guidelines 2023', url: 'https://kviconline.gov.in/pmegp' },
  ],
  detected_language: 'hi',
}

export async function sendAdvisoryChat({ message, language, context }) {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_RESPONSE
  }
  return postJson('/advisory-chat', { message, language, context })
}
