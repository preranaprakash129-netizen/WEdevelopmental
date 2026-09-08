import { isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #2 POST /calculator
const MOCK_RESPONSE = {
  project_cost: 200000,
  scheme_selected: { name: 'PMEGP', subsidy_percent: 25 },
  loan_amount: 150000,
  emi_schedule: Array.from({ length: 12 }, (_, i) => {
    const month = i + 1
    const outstanding = 150000 - month * 3100
    return {
      month,
      emi: 4200,
      principal_component: 3100 + i * 40,
      interest_component: 1100 - i * 40,
      outstanding_balance: Math.max(outstanding, 0),
    }
  }),
  moratorium: { months: 6, reason: 'PMEGP standard moratorium for dairy category' },
  working_capital: 25000,
}

export async function fetchCalculator({ margin_capital, category, location, requested_loan_amount }) {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_RESPONSE
  }
  return postJson('/calculator', { margin_capital, category, location, requested_loan_amount })
}
