import { isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #3 POST /ess-score
const MOCK_RESPONSE = {
  ess_score: 61.0,
  sub_scores: {
    financial_health: 55.0,
    market_stability: 70.0,
    operational_maturity: 58.0,
    growth_potential: 61.0,
  },
  attribution: [
    { feature: 'monthly_revenue', impact: 8.2 },
    { feature: 'years_operating', impact: -3.1 },
    { feature: 'has_bank_account', impact: 2.4 },
  ],
  top_improvement_action: {
    action: 'Open a dedicated business bank account to formalize cash flow tracking',
    expected_score_delta: 4.5,
  },
}

// Exactly one of business_id or profile_data is required per the contract.
export async function fetchEssScore({ business_id, profile_data }) {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_RESPONSE
  }
  return postJson('/ess-score', business_id ? { business_id } : { profile_data })
}
