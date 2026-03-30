import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRun } from '../lib/api'

function ScoreBar({ score }) {
  const pct = (score / 10) * 100
  const color = score >= 7 ? 'bg-green-500' : score >= 5 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-semibold ${score >= 7 ? 'text-green-600 dark:text-green-400' : score >= 5 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
        {score}/10
      </span>
    </div>
  )
}

export default function RunView() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [liveResults, setLiveResults] = useState([])
  const [summary, setSummary] = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [expanded, setExpanded] = useState({})
  const esRef = useRef(null)

  const startStream = useCallback(() => {
    setStreaming(true)
    const es = new EventSource(`/api/runs/${id}/stream`)
    esRef.current = es

    es.onmessage = (e) => {
      const event = JSON.parse(e.data)
      if (event.type === 'result') {
        setLiveResults(prev => {
          const next = [...prev]
          const idx = next.findIndex(r => r.run_result_id === event.run_result_id)
          if (idx === -1) next.push(event)
          else next[idx] = event
          return next
        })
      } else if (event.type === 'complete') {
        setSummary(event)
        setStreaming(false)
        es.close()
        // reload full run to get response_text + reasoning
        getRun(id).then(r => { setRun(r); setLiveResults(r.results || []) })
      } else if (event.type === 'done') {
        setStreaming(false)
        es.close()
        getRun(id).then(r => { setRun(r); setLiveResults(r.results || []); setSummary(r.summary) })
      }
    }
    es.onerror = () => { setStreaming(false); es.close() }
  }, [id])

  useEffect(() => {
    getRun(id).then(r => {
      setRun(r)
      if (r.status === 'completed') {
        setLiveResults(r.results || [])
        setSummary(r.summary)
      } else if (r.status === 'running' || r.status === 'pending') {
        startStream()
      }
    })
    return () => esRef.current?.close()
  }, [id, startStream])

  const toggle = (id) => setExpanded(e => ({ ...e, [id]: !e[id] }))

  if (!run) return <div className="text-gray-400 text-sm">Loading...</div>

  const results = run.status === 'completed' ? (run.results || []) : liveResults
  const totalCases = run.status === 'completed' ? results.length : (summary?.total_cases || '?')

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline">← Dashboard</Link>
        <div className="flex items-center justify-between mt-1">
          <h1 className="text-xl font-semibold">Run #{run.id}</h1>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            run.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' :
            run.status === 'running' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
            'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
          }`}>
            {streaming ? 'running…' : run.status}
          </span>
        </div>
        <p className="text-sm text-gray-400 mt-1">{run.model_name}</p>
      </div>

      {/* Summary */}
      {(summary || run.summary) && (() => {
        const s = summary || run.summary
        return (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Avg Score', value: s.avg_score?.toFixed(1) ?? '—' },
              { label: 'Pass Rate', value: s.pass_rate != null ? `${Math.round(s.pass_rate * 100)}%` : '—' },
              { label: 'Completed', value: `${s.completed_cases ?? results.length}/${s.total_cases ?? totalCases}` },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3 text-center">
                <div className="text-xs text-gray-400">{label}</div>
                <div className="text-xl font-semibold text-cyan-600 dark:text-cyan-400 mt-1">{value}</div>
              </div>
            ))}
          </div>
        )
      })()}

      {/* Live results */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Results ({results.length}/{totalCases})
          </h2>
          {streaming && (
            <span className="text-xs text-amber-600 dark:text-amber-400 animate-pulse">Live</span>
          )}
        </div>

        {results.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            {streaming ? 'Waiting for results…' : 'No results'}
          </p>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {results.map((r, i) => {
              const score = r.score ?? 0
              const passed = r.pass ?? r.pass_
              const resultId = r.id ?? r.run_result_id
              const isExpanded = expanded[resultId]

              return (
                <div key={resultId ?? i} className="px-4 py-3">
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggle(resultId)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-6">#{r.index ?? i + 1}</span>
                      <span className={`text-xs font-medium ${passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {passed ? 'Pass' : 'Fail'}
                      </span>
                      {score != null && <ScoreBar score={score} />}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      {r.latency_ms != null && <span>{r.latency_ms}ms</span>}
                      <span>{isExpanded ? '▲' : '▼'}</span>
                    </div>
                  </div>

                  {isExpanded && (run.results || []).find(x => x.id === resultId) && (() => {
                    const full = run.results.find(x => x.id === resultId)
                    return (
                      <div className="mt-3 space-y-3 text-sm">
                        {full.response_text && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Response</div>
                            <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap text-xs bg-gray-50 dark:bg-gray-800 rounded-lg p-3">{full.response_text}</div>
                          </div>
                        )}
                        {full.reasoning && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Judge Reasoning</div>
                            <div className="text-gray-600 dark:text-gray-400 text-xs italic">{full.reasoning}</div>
                          </div>
                        )}
                        {full.strengths?.length > 0 && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Strengths</div>
                            <ul className="space-y-0.5">
                              {full.strengths.map((s, i) => (
                                <li key={i} className="text-xs text-green-600 dark:text-green-400">✓ {s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {full.weaknesses?.length > 0 && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Weaknesses</div>
                            <ul className="space-y-0.5">
                              {full.weaknesses.map((w, i) => (
                                <li key={i} className="text-xs text-red-600 dark:text-red-400">✗ {w}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )
                  })()}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {run.status === 'completed' && (
        <div className="flex gap-3">
          <Link
            to={`/suite/${run.suite_id}`}
            className="border border-gray-300 dark:border-gray-700 hover:border-gray-500 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm px-4 py-2 rounded-lg transition-colors"
          >
            Back to Suite
          </Link>
        </div>
      )}
    </div>
  )
}
