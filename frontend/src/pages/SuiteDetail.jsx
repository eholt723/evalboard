import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSuite, addCase, deleteCase, createRun, getRuns } from '../lib/api'

const MODELS = ['llama-3.1-8b-instant', 'llama-3.3-70b-versatile']

export default function SuiteDetail() {
  const { id } = useParams()
  const [suite, setSuite] = useState(null)
  const [runs, setRuns] = useState([])
  const [model, setModel] = useState(MODELS[0])
  const [running, setRunning] = useState(false)
  const [showCaseForm, setShowCaseForm] = useState(false)
  const [caseForm, setCaseForm] = useState({ input: '', expected: '', criteria: '' })
  const [addingCase, setAddingCase] = useState(false)

  const load = () => Promise.all([
    getSuite(id).then(setSuite),
    getRuns().then(all => setRuns(all.filter(r => r.suite_id === parseInt(id)))),
  ])

  useEffect(() => { load() }, [id])

  const handleRun = async () => {
    setRunning(true)
    try {
      const run = await createRun({ suite_id: parseInt(id), model_name: model })
      window.location.href = `/run/${run.id}`
    } catch (e) {
      alert(e.message)
      setRunning(false)
    }
  }

  const handleAddCase = async (e) => {
    e.preventDefault()
    if (!caseForm.input.trim()) return
    setAddingCase(true)
    try {
      await addCase(id, caseForm)
      setCaseForm({ input: '', expected: '', criteria: '' })
      setShowCaseForm(false)
      getSuite(id).then(setSuite)
    } finally {
      setAddingCase(false)
    }
  }

  const handleDeleteCase = async (caseId) => {
    if (!confirm('Delete this test case?')) return
    await deleteCase(id, caseId)
    getSuite(id).then(setSuite)
  }

  if (!suite) return <div className="text-gray-400 text-sm">Loading...</div>

  return (
    <div className="space-y-6">
      <div>
        <Link to="/suites" className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline">← Suites</Link>
        <h1 className="text-xl font-semibold mt-1">{suite.name}</h1>
        {suite.description && <p className="text-sm text-gray-400 mt-1">{suite.description}</p>}
      </div>

      {/* Run controls */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 space-y-3">
        <h2 className="text-sm font-medium">Start a Run</h2>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={model}
            onChange={e => setModel(e.target.value)}
            className="bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-cyan-600"
          >
            {MODELS.map(m => <option key={m}>{m}</option>)}
          </select>
          <button
            onClick={handleRun}
            disabled={running || suite.cases.length === 0}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            {running ? 'Starting…' : 'Run'}
          </button>
          {suite.cases.length === 0 && (
            <span className="text-xs text-gray-400">Add test cases first</span>
          )}
        </div>
      </div>

      {/* Test cases */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Test Cases ({suite.cases.length})
          </h2>
          <button
            onClick={() => setShowCaseForm(f => !f)}
            className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline"
          >
            {showCaseForm ? 'Cancel' : '+ Add Case'}
          </button>
        </div>

        {showCaseForm && (
          <form onSubmit={handleAddCase} className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 space-y-2">
            <textarea
              value={caseForm.input}
              onChange={e => setCaseForm(f => ({ ...f, input: e.target.value }))}
              placeholder="Input (user message)"
              rows={2}
              className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600 resize-none"
            />
            <textarea
              value={caseForm.expected}
              onChange={e => setCaseForm(f => ({ ...f, expected: e.target.value }))}
              placeholder="Expected output"
              rows={2}
              className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600 resize-none"
            />
            <input
              value={caseForm.criteria}
              onChange={e => setCaseForm(f => ({ ...f, criteria: e.target.value }))}
              placeholder="Evaluation criteria"
              className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600"
            />
            <button
              type="submit"
              disabled={addingCase || !caseForm.input.trim()}
              className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
            >
              {addingCase ? 'Adding…' : 'Add Case'}
            </button>
          </form>
        )}

        {suite.cases.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No test cases yet</p>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {suite.cases.map((c, i) => (
              <div key={c.id} className="px-4 py-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs text-gray-400 mt-0.5 shrink-0">#{i + 1}</span>
                  <div className="flex-1 space-y-1 min-w-0">
                    <p className="text-sm text-gray-800 dark:text-gray-200">{c.input}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400"><span className="font-medium">Expected:</span> {c.expected}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400"><span className="font-medium">Criteria:</span> {c.criteria}</p>
                  </div>
                  <button
                    onClick={() => handleDeleteCase(c.id)}
                    className="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors shrink-0"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Run history */}
      {runs.length > 0 && (
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
            <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400">Run History</h2>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {runs.map(r => (
              <Link
                key={r.id}
                to={`/run/${r.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors text-sm"
              >
                <span className="text-gray-700 dark:text-gray-300">{r.model_name}</span>
                <div className="flex items-center gap-3">
                  {r.summary && <span className="text-cyan-600 dark:text-cyan-400 font-semibold">{r.summary.avg_score?.toFixed(1)}</span>}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    r.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' :
                    r.status === 'running' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
                    'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  }`}>{r.status}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
