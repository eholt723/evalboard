import { Link } from 'react-router-dom'

const steps = [
  { n: 1, title: 'Define Test Cases', desc: 'Write a prompt input, what a good response should include, and how to judge it — factual accuracy, tone, completeness, whatever matters for your use case.' },
  { n: 2, title: 'Choose Models', desc: 'Pick one or two LLMs to run against the suite. EvalBoard supports any model available on Groq — llama-3.1-8b-instant, llama-3.3-70b-versatile, and more.' },
  { n: 3, title: 'Run in Parallel', desc: 'All test cases execute simultaneously using asyncio with a concurrency semaphore. Results stream to your screen live as each one finishes.' },
  { n: 4, title: 'Score with an LLM Judge', desc: 'A second Groq call evaluates each response against the expected output and criteria, returning a 1–10 score, pass/fail, strengths, weaknesses, and reasoning.' },
  { n: 5, title: 'Track Over Time', desc: 'The dashboard plots score trends across runs, ranks models by average score and pass rate, and lets you do side-by-side comparisons of any two runs.' },
]

const achievements = [
  'Runs all test cases in parallel using asyncio with configurable concurrency',
  'Streams live results to the browser via SSE as each case completes',
  'LLM-as-judge scoring returns structured JSON: score, pass/fail, strengths, weaknesses, reasoning',
  'Fan-out SSE broadcaster allows multiple clients to watch the same run simultaneously',
  'Reconnecting clients replay missed events from history',
  'Prompt variant versioning — create multiple system prompts and A/B test against the same suite',
  'Dashboard tracks score trends, model leaderboard, and per-suite pass rates',
  'Side-by-side run comparison with per-case score diffs',
  'PostgreSQL on Neon with async SQLAlchemy + Alembic migrations',
  'Pre-loaded demo content — three suites ready to run on first load',
]

const stack = [
  { name: 'FastAPI', role: 'Async REST API + SSE streaming' },
  { name: 'asyncio', role: 'Parallel LLM inference with semaphore' },
  { name: 'Groq', role: 'LLM inference + judge model' },
  { name: 'PostgreSQL', role: 'Persistent storage via Neon' },
  { name: 'SQLAlchemy', role: 'Async ORM with Alembic migrations' },
  { name: 'React', role: 'Frontend UI with live SSE updates' },
  { name: 'Recharts', role: 'Score trend and comparison charts' },
  { name: 'Tailwind CSS', role: 'Utility-first styling, dark mode' },
  { name: 'Vite', role: 'Frontend build and dev server' },
  { name: 'Docker', role: 'Containerized deployment' },
  { name: 'Hugging Face Spaces', role: 'Hosting' },
  { name: 'GitHub Actions', role: 'CI on every push' },
]

export default function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-16">

      {/* Hero */}
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">
          Systematic LLM Evaluation, <span className="text-cyan-600 dark:text-cyan-400">live.</span>
        </h1>
        <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
          EvalBoard is a tool for measuring LLM quality in a repeatable, structured way. You define test cases with expected outputs and scoring criteria, run them against one or more models, and watch scores populate live as results stream in. The judge — a separate LLM call — tells you not just whether a response passed, but exactly why it did or didn't.
        </p>
        <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
          The core demo: the same 10 test cases run against <span className="font-mono text-sm text-cyan-600 dark:text-cyan-400">llama-3.1-8b-instant</span> and <span className="font-mono text-sm text-cyan-600 dark:text-cyan-400">llama-3.3-70b-versatile</span> simultaneously. See where the smaller model underperforms and why.
        </p>
      </section>

      {/* How It Works */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">How It Works</h2>
        <div className="space-y-0">
          {steps.map((step, i) => (
            <div key={step.n} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-cyan-600 text-white text-sm font-semibold flex items-center justify-center shrink-0">
                  {step.n}
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 bg-gray-200 dark:bg-gray-800 my-1" />
                )}
              </div>
              <div className={`pb-6 ${i === steps.length - 1 ? '' : ''}`}>
                <div className="text-sm font-semibold text-gray-800 dark:text-gray-200 mt-1">{step.title}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{step.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* What Was Built */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">What Was Built</h2>
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4">
          <ul className="space-y-2">
            {achievements.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span className="text-cyan-500 font-semibold mt-0.5 shrink-0">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Tech Stack</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {stack.map(({ name, role }) => (
            <div key={name} className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
              <div className="text-sm font-semibold text-gray-800 dark:text-gray-200">{name}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{role}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Links */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Links</h2>
        <div className="flex gap-3 flex-wrap">
          <Link
            to="/"
            className="bg-cyan-600 hover:bg-cyan-500 text-white text-sm px-5 py-2.5 rounded-lg transition-colors"
          >
            Try the App
          </Link>
          <a
            href="https://github.com/eholt723/evalboard"
            target="_blank"
            rel="noreferrer"
            className="border border-gray-300 dark:border-gray-700 hover:border-gray-500 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 text-sm px-5 py-2.5 rounded-lg transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </section>

    </div>
  )
}
