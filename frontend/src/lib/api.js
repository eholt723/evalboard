const BASE = '/api'

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

// Suites
export const getSuites = () => req('/suites')
export const getSuite = (id) => req(`/suites/${id}`)
export const createSuite = (data) => req('/suites', { method: 'POST', body: JSON.stringify(data) })
export const deleteSuite = (id) => req(`/suites/${id}`, { method: 'DELETE' })
export const addCase = (suiteId, data) => req(`/suites/${suiteId}/cases`, { method: 'POST', body: JSON.stringify(data) })
export const deleteCase = (suiteId, caseId) => req(`/suites/${suiteId}/cases/${caseId}`, { method: 'DELETE' })

// Prompts
export const getPrompts = () => req('/prompts')
export const createPrompt = (data) => req('/prompts', { method: 'POST', body: JSON.stringify(data) })
export const deletePrompt = (id) => req(`/prompts/${id}`, { method: 'DELETE' })

// Runs
export const getRuns = () => req('/runs')
export const getRun = (id) => req(`/runs/${id}`)
export const createRun = (data) => req('/runs', { method: 'POST', body: JSON.stringify(data) })
export const compareRuns = (a, b) => req(`/dashboard/compare/${a}/${b}`)

// Dashboard
export const getRecentRuns = (limit = 10) => req(`/dashboard/recent-runs?limit=${limit}`)
export const getScoreTrends = (suiteId) => req(`/dashboard/score-trends${suiteId ? `?suite_id=${suiteId}` : ''}`)
export const getLeaderboard = () => req('/dashboard/leaderboard')
export const getPassRateBySuite = () => req('/dashboard/pass-rate-by-suite')
