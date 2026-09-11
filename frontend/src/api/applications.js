import { getJson, isMockMode, mockDelay, postJson } from './client.js'

// Shape matches docs/api-contract.md #5 POST/GET /applications.
let mockApplications = [
  {
    id: 1,
    applicant_name: null,
    category: 'dairy',
    location: 'Rampur',
    ess_score: 61.0,
    status: 'Under review',
    created_at: '2026-09-08T10:15:00Z',
  },
  {
    id: 2,
    applicant_name: null,
    category: 'tailoring',
    location: 'Sitapur',
    ess_score: 74.2,
    status: 'Approved',
    created_at: '2026-09-07T09:00:00Z',
  },
]

export async function fetchApplications() {
  if (isMockMode()) {
    await mockDelay()
    return { applications: mockApplications }
  }
  return getJson('/applications')
}

// Shape matches GET /api/applications/insights (backend-api/app/main.py). Real
// aggregates computed from the applications table. matched_scheme_breakdown is null
// here too, matching the real endpoint's honest gap -- scheme-match results aren't
// persisted anywhere yet, so this can't be built from real data (see that endpoint's
// docstring/comment for why).
const MOCK_INSIGHTS = {
  total_applications: 2,
  category_breakdown: [
    { category: 'dairy', count: 1 },
    { category: 'tailoring', count: 1 },
  ],
  ess_score_histogram: {
    buckets: [
      { range: '0-20', count: 0 },
      { range: '20-40', count: 0 },
      { range: '40-60', count: 0 },
      { range: '60-80', count: 1 },
      { range: '80-100', count: 1 },
    ],
    unscored_count: 0,
  },
  matched_scheme_breakdown: null,
}

export async function fetchApplicationInsights() {
  if (isMockMode()) {
    await mockDelay()
    return MOCK_INSIGHTS
  }
  return getJson('/applications/insights')
}

// Fire-and-forget from the wizard's perspective: a failure here (e.g. DB not up yet)
// should never block an applicant from reaching the dashboard, so callers should catch
// and ignore errors rather than surfacing them as a wizard-blocking failure.
export async function submitApplication({ location, category, ess_score, status }) {
  if (isMockMode()) {
    await mockDelay(150)
    const row = {
      id: mockApplications.length + 1,
      applicant_name: null,
      location,
      category,
      ess_score: ess_score ?? null,
      status: status || 'Under review',
      created_at: new Date().toISOString(),
    }
    mockApplications = [row, ...mockApplications]
    return row
  }
  return postJson('/applications', { location, category, ess_score, status })
}
