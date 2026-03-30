import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSuites, createSuite, deleteSuite } from '../lib/api'

export default function Suites() {
  const [suites, setSuites] = useState([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)

  const load = () => getSuites().then(setSuites)
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    try {
      await createSuite({ name: name.trim(), description: desc.trim() || null })
      setName(''); setDesc(''); setShowForm(false)
      load()
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.preventDefault()
    if (!confirm('Delete this suite and all its test cases?')) return
    await deleteSuite(id)
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Test Suites</h1>
        <button
          onClick={() => setShowForm(f => !f)}
          className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-3 py-1.5 rounded-lg transition-colors"
        >
          {showForm ? 'Cancel' : 'New Suite'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 space-y-3">
          <h2 className="text-sm font-medium">Create Suite</h2>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Suite name"
            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600"
          />
          <input
            value={desc}
            onChange={e => setDesc(e.target.value)}
            placeholder="Description (optional)"
            className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyan-600"
          />
          <button
            type="submit"
            disabled={creating || !name.trim()}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            {creating ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
        {suites.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-10">No suites yet</p>
        ) : suites.map(s => (
          <Link
            key={s.id}
            to={`/suite/${s.id}`}
            className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <div>
              <div className="text-sm font-medium text-gray-800 dark:text-gray-200">{s.name}</div>
              {s.description && <div className="text-xs text-gray-400 mt-0.5">{s.description}</div>}
            </div>
            <button
              onClick={(e) => handleDelete(s.id, e)}
              className="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors ml-4"
            >
              Delete
            </button>
          </Link>
        ))}
      </div>
    </div>
  )
}
