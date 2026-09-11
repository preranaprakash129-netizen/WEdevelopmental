import { isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #6 POST /scheme-match. Unlike the mock
// data for the other endpoints, this one is not hand-invented — it is the
// real, saved output of the trained classifier for this exact profile
// (services/advisory-llm/models/scheme_match_report.txt), so mock mode shows
// the same kind of answer the trained model actually gives.
const MOCK_RESPONSE = {
  request_id: 'mock-scheme-match',
  results: [
    {
      scheme: 'Karnataka Udyogini',
      display_name: 'Udyogini Scheme (Karnataka)',
      confidence: 0.6399,
      why: [
        'Reserved for women entrepreneurs, which matches the applicant.',
        'Open to existing businesses, not just new ones.',
        "Requested amount fits the scheme's Rs.0-Rs.300,000 range.",
      ],
      url: 'https://kswdc.karnataka.gov.in/',
      match_breakdown: { category_fit: 1.0, loan_amount_fit: 1.0, eligibility_fit: 1.0, priority_boost_fit: 1.0 },
      improvement_tips: [],
    },
    {
      scheme: 'PMFME',
      display_name: 'Pradhan Mantri Formalisation of Micro Food Processing Enterprises (PMFME)',
      confidence: 0.3428,
      why: [
        "Specifically targets the 'dairy' category.",
        'Open to existing businesses, not just new ones.',
        "Requested amount fits the scheme's Rs.0-Rs.1,000,000 range.",
      ],
      url: 'https://pmfme.mofpi.gov.in/',
      match_breakdown: { category_fit: 1.0, loan_amount_fit: 1.0, eligibility_fit: 1.0, priority_boost_fit: 0.5 },
      improvement_tips: [],
    },
    {
      scheme: 'CGTMSE',
      display_name: 'Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)',
      confidence: 0.0094,
      why: [
        'Open to existing businesses, not just new ones.',
        "Requested amount fits the scheme's Rs.0-Rs.100,000,000 range.",
        'Bank loan can get up to 85% collateral-free guarantee coverage.',
      ],
      url: 'https://www.cgtmse.in/',
      match_breakdown: { category_fit: 1.0, loan_amount_fit: 1.0, eligibility_fit: 1.0, priority_boost_fit: 0.0 },
      improvement_tips: [
        'Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE) offers a higher subsidy/coverage tier for SC/ST or women applicants -- this profile doesn\'t currently qualify for that higher tier, which is part of why the overall match isn\'t stronger.',
      ],
    },
  ],
  model_feature_importance: {
    category: 0.4004,
    requested_amount: 0.2175,
    margin_capital: 0.0858,
    annual_family_income: 0.0635,
    gender: 0.0489,
    location_type: 0.0473,
    monthly_revenue: 0.0415,
    years_operating: 0.0359,
    is_new_business: 0.0335,
    is_sc_st: 0.0256,
  },
}

// profile: { category, is_new_business, years_operating, gender, is_sc_st,
//            location_type, annual_family_income, monthly_revenue,
//            requested_amount, margin_capital } — see docs/api-contract.md #6.
export async function fetchSchemeMatch(profile) {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_RESPONSE
  }
  return postJson('/scheme-match', profile)
}
