import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { getRecentRuns, getScoreTrends, getLeaderboard, getPassRateBySuite, getSuites, createRun } from '../lib/api'

function ScoreBadge({ score }) {
  if (score == null) return <span className="text-gray-400 text-xs">—</span>
  const color = score >= 7 ? 'text-green-600 dark:text-green-400' : score >= 5 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
  return <span className={`font-semibold ${color}`}>{score.toFixed(1)}</span>
}

function PassRate({ rate }) {
  if (rate == null) return <span className="text-gray-400 text-xs">—</span>
  const pct = Math.round(rate * 100)
  const color = pct >= 70 ? 'text-green-600 dark:text-green-400' : pct >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
  return <span className={`font-semibold ${color}`}>{pct}%</span>
}

const MODEL_COLORS = {
  'llama-3.1-8b-instant': '#06b6d4',
  'llama-3.3-70b-versatile': '#8b5cf6',
}
const FALLBACK_COLORS = ['#06b6d4', '#8b5cf6', '#f59e0b', '#10b981']

const QUICK_STARTS = [
  {
    label: 'Customer Support — Llama 8B',
    suite: 'Customer Support Quality',
    model: 'llama-3.1-8b-instant',
    description: '8 customer service scenarios scored live against the smaller model',
  },
  {
    label: 'Customer Support — Llama 70B',
    suite: 'Customer Support Quality',
    model: 'llama-3.3-70b-versatile',
    description: 'Same 8 cases against the 70B — watch the score gap open up',
  },
  {
    label: 'Code Review — Llama 70B',
    suite: 'Code Review Accuracy',
    model: 'llama-3.3-70b-versatile',
    description: 'SQL injection, resource leaks, hardcoded secrets — does it catch them?',
  },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [trends, setTrends] = useState([])
  const [leaderboard, setLeaderboard] = useState([])
  const [passBySuite, setPassBySuite] = useState([])
  const [suites, setSuites] = useState([])
  const [loading, setLoading] = useState(true)
  const [launching, setLaunching] = useState({})

  useEffect(() => {
    Promise.all([getRecentRuns(), getScoreTrends(), getLeaderboard(), getPassRateBySuite(), getSuites()])
      .then(([r, t, l, p, s]) => { setRuns(r); setTrends(t); setLeaderboard(l); setPassBySuite(p); setSuites(s) })
      .finally(() => setLoading(false))
  }, [])

  const handleQuickStart = async (qs) => {
    setLaunching(prev => ({ ...prev, [qs.label]: true }))
    try {
      const suite = suites.find(s => s.name === qs.suite)
      if (!suite) throw new Error(`Suite "${qs.suite}" not found — run seed.py to load demo data`)
      const run = await createRun({ suite_id: suite.id, model_name: qs.model })
      navigate(`/run/${run.id}`)
    } catch (e) {
      alert(e.message)
      setLaunching(prev => ({ ...prev, [qs.label]: false }))
    }
  }

  const models = [...new Set(trends.map(t => t.model_name))]

  const chartData = (() => {
    const byDate = {}
    trends.forEach(t => {
      const key = t.started_at.slice(0, 16)
      if (!byDate[key]) byDate[key] = { date: key }
      byDate[key][t.model_name] = t.avg_score
    })
    return Object.values(byDate)
  })()

  if (loading) return <div className="text-gray-400 text-sm">Loading...</div>

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <Link to="/suites" className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-3 py-1.5 rounded-lg transition-colors">
          New Run
        </Link>
      </div>

      {/* Quick Start */}
      <div className="rounded-xl border border-cyan-200 dark:border-cyan-900/50 bg-cyan-50/50 dark:bg-cyan-950/20 p-4">
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Quick Start</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Fire a live run and watch scores stream in real time</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {QUICK_STARTS.map((qs) => (
            <div
              key={qs.label}
              className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 flex flex-col gap-3"
            >
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-800 dark:text-gray-200 leading-snug">{qs.label}</div>
                <div className="text-xs text-gray-400 mt-1 leading-relaxed">{qs.description}</div>
              </div>
              <button
                onClick={() => handleQuickStart(qs)}
                disabled={!!launching[qs.label]}
                className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
              >
                {launching[qs.label] ? 'Starting…' : 'Run Live'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Score trend chart */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
        <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Score Trends</h2>
        {chartData.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No completed runs yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} tickLine={false} width={28} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {models.map((m, i) => (
                <Line
                  key={m}
                  type="monotone"
                  dataKey={m}
                  stroke={MODEL_COLORS[m] || FALLBACK_COLORS[i % FALLBACK_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Model leaderboard */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Model Leaderboard</h2>
          {leaderboard.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <div className="space-y-2">
              {leaderboard.map((m, i) => (
                <div key={m.model_name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                    <span className="truncate text-gray-700 dark:text-gray-300">{m.model_name}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <ScoreBadge score={m.avg_score} />
                    <PassRate rate={m.avg_pass_rate} />
                    <span className="text-xs text-gray-400">{m.run_count}r</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pass rate by suite */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Pass Rate by Suite</h2>
          {passBySuite.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <div className="space-y-2">
              {passBySuite.map(s => (
                <div key={s.suite_name} className="flex items-center justify-between text-sm">
                  <span className="truncate text-gray-700 dark:text-gray-300">{s.suite_name}</span>
                  <div className="flex items-center gap-3 shrink-0">
                    <PassRate rate={s.avg_pass_rate} />
                    <span className="text-xs text-gray-400">{s.run_count}r</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent runs */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent Runs</h2>
        </div>
        {runs.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No runs yet — use Quick Start above</p>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {runs.map(r => (
              <Link
                key={r.run_id}
                to={`/run/${r.run_id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <div>
                  <div className="text-sm font-medium text-gray-800 dark:text-gray-200">{r.suite_name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{r.model_name}</div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <ScoreBadge score={r.avg_score} />
                  <PassRate rate={r.pass_rate} />
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    r.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' :
                    r.status === 'running' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
                    'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  }`}>
                    {r.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
