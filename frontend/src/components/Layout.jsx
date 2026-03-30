import { NavLink } from 'react-router-dom'
import { useEffect, useState } from 'react'

export default function Layout({ children }) {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('dark')
    return stored !== null ? stored === 'true' : true
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('dark', dark)
  }, [dark])

  const navClass = ({ isActive }) =>
    isActive
      ? 'text-cyan-600 dark:text-cyan-400 font-medium'
      : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors'

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <header className="border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <span className="text-cyan-600 dark:text-cyan-400 font-semibold tracking-tight text-lg">
            EvalBoard
          </span>
          <nav className="flex items-center gap-6 text-sm">
            <NavLink to="/" end className={navClass}>Dashboard</NavLink>
            <NavLink to="/suites" className={navClass}>Suites</NavLink>
            <NavLink to="/prompts" className={navClass}>Prompts</NavLink>
            <NavLink to="/about" className={navClass}>About</NavLink>
          </nav>
          <button
            onClick={() => setDark(d => !d)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle dark mode"
          >
            {dark ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {children}
      </main>

      <footer className="relative border-t border-gray-200 dark:border-gray-800 text-center text-xs text-gray-400 dark:text-gray-600 py-4 mt-12">
        EvalBoard — LLM Evaluation Dashboard
        <span className="fixed bottom-3 right-4 text-right text-xs text-gray-400 dark:text-gray-600 pointer-events-none select-none">
          Created by Eric Holt
        </span>
      </footer>
    </div>
  )
}
