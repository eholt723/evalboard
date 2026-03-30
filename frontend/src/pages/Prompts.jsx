import { useEffect, useState } from 'react'
import { getPrompts, createPrompt, deletePrompt } from '../lib/api'

export default function Prompts() {
  const [prompts, setPrompts] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [creating, setCreating] = useState(false)
  const [expanded, setExpanded] = useState({})

  const load = () => getPrompts().then(setPrompts)
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim() || !systemPrompt.trim()) return
    setCreating(true)
    try {
      await createPrompt({ name: name.trim(), system_prompt: systemPrompt.trim() })
      setName(''); setSystemPrompt(''); setShowForm(false)
      load()
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this prompt variant?')) return
    await deletePrompt(id)
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Prompt Variants</h1>
        <button
          onClick={() => setShowForm(f => !f)}
          className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-3 py-1.5 rounded-lg transition-colors"
        >
          {showForm ? 'Cancel' : 'New Variant'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 space-y-3">
          <h2 className="text-sm font-medium">Create Prompt Variant</h2>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Variant name (e.g. concise, detailed)"
            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600"
          />
          <textarea
            value={systemPrompt}
            onChange={e => setSystemPrompt(e.target.value)}
            placeholder="System prompt content"
            rows={5}
            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600 resize-none font-mono"
          />
          <button
            type="submit"
            disabled={creating || !name.trim() || !systemPrompt.trim()}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            {creating ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
        {prompts.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-10">No prompt variants yet</p>
        ) : prompts.map(p => (
          <div key={p.id} className="px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-800 dark:text-gray-200">{p.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">v{p.version}</div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setExpanded(e => ({ ...e, [p.id]: !e[p.id] }))}
                  className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline"
                >
                  {expanded[p.id] ? 'Hide' : 'View'}
                </button>
                <button
                  onClick={() => handleDelete(p.id)}
                  className="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
            {expanded[p.id] && (
              <pre className="mt-3 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 whitespace-pre-wrap font-mono">
                {p.system_prompt}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
