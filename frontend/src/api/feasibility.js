import { isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #1 POST /feasibility
const MOCK_RESPONSE = {
  market_reach: {
    estimated_customers: 1200,
    radius_km: 3.5,
  },
  competitor_list: [
    { name: 'Shree Dairy', category: 'dairy', distance_km: 1.2 },
    { name: 'Gopal Milk Center', category: 'dairy', distance_km: 2.8 },
  ],
  swot: {
    strengths: ['Low local competition density', 'Steady demand for milk products'],
    weaknesses: ['High cold-chain setup cost'],
    opportunities: ['Government dairy subsidy schemes available'],
    threats: ['Seasonal demand fluctuation'],
  },
  pricing_bands: { low: 40, median: 55, high: 70 },
  feasibility_score: 72.5,
  confidence_range: { low: 64.0, high: 79.0 },
}

export async function fetchFeasibility({ location, category, margin_capital }) {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_RESPONSE
  }
  return postJson('/feasibility', { location, category, margin_capital })
}
