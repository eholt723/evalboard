"""
Seed the database with 3 demo test suites and pre-execute comparison runs.

Usage (from the backend directory with .venv active):
    python seed.py

Idempotent: skips suites and completed runs that already exist.
Requires GROQ_API_KEY and DATABASE_URL in .env.
"""
import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.engine.runner import execute_run
from app.models.case import TestCase
from app.models.run import Run
from app.models.suite import TestSuite

SUITES = [
    {
        "name": "Customer Support Quality",
        "description": (
            "Evaluates how well a model handles common customer service scenarios "
            "— empathy, accuracy, and actionability."
        ),
        "cases": [
            {
                "input": "I ordered a laptop 2 weeks ago and it still hasn't arrived. My order number is #45829.",
                "expected": (
                    "Acknowledge the delay, apologize sincerely, offer to look up the order, "
                    "and provide tracking information or a concrete next step."
                ),
                "criteria": "Empathetic tone, actionable next steps, professional language, directly addresses the delay.",
            },
            {
                "input": "Your product broke after just 3 days of use! I want a full refund immediately.",
                "expected": (
                    "Express empathy and apology, explain the refund process clearly, "
                    "provide a timeline, and optionally offer a replacement."
                ),
                "criteria": "Calm and empathetic, clear explanation of the resolution process, avoids defensiveness.",
            },
            {
                "input": "I've been charged twice for my subscription this month. This is completely unacceptable.",
                "expected": (
                    "Acknowledge and apologize for the duplicate charge, confirm it will be refunded, "
                    "and provide a specific timeline."
                ),
                "criteria": "Takes ownership of the error, specific resolution timeline, professional and reassuring.",
            },
            {
                "input": "How do I reset my password? I can't log in to my account.",
                "expected": (
                    "Provide clear step-by-step instructions for resetting the password, "
                    "mention where to find the reset link, and offer further assistance."
                ),
                "criteria": "Clear step-by-step instructions, friendly tone, complete without unnecessary information.",
            },
            {
                "input": "I received the wrong item. I ordered a blue shirt in size M but received a green one in size L.",
                "expected": (
                    "Apologize for the error, arrange a free return, confirm the correct item "
                    "will be reshipped promptly, and provide a return label."
                ),
                "criteria": "Apologetic tone, proactive resolution, clear next steps for return and reshipment.",
            },
            {
                "input": "Can you explain your return policy? I'm considering returning a purchase I made last week.",
                "expected": (
                    "Provide a complete explanation of the return window, accepted conditions, "
                    "the return process, and any relevant exceptions."
                ),
                "criteria": "Complete and accurate policy information, easy to understand, mentions conditions or exceptions.",
            },
            {
                "input": "I've been waiting on hold for over 45 minutes. This is absolutely ridiculous!",
                "expected": (
                    "Sincerely apologize for the wait without making excuses, acknowledge the frustration, "
                    "and quickly pivot to solving the underlying issue."
                ),
                "criteria": "Sincere apology, no deflection or excuses, immediately focuses on the customer's underlying need.",
            },
            {
                "input": "The app keeps crashing at checkout. I've already tried reinstalling it twice.",
                "expected": (
                    "Thank the customer for the troubleshooting steps already taken, acknowledge the issue, "
                    "provide additional diagnostic steps, and escalate to technical support if needed."
                ),
                "criteria": "Acknowledges prior troubleshooting, provides new actionable steps, clear escalation path.",
            },
        ],
    },
    {
        "name": "Code Review Accuracy",
        "description": (
            "Tests whether a model can identify real bugs, security issues, "
            "and style problems in code snippets."
        ),
        "cases": [
            {
                "input": (
                    "Review this Python function:\n\n"
                    "def get_user(username):\n"
                    "    query = f\"SELECT * FROM users WHERE username = '{username}'\"\n"
                    "    return db.execute(query)"
                ),
                "expected": (
                    "Identify the SQL injection vulnerability, explain why string interpolation in SQL "
                    "is dangerous, and provide a corrected version using parameterized queries."
                ),
                "criteria": (
                    "Correctly identifies SQL injection as the primary issue, "
                    "explains the security risk, provides corrected parameterized query code."
                ),
            },
            {
                "input": (
                    "Review this JavaScript:\n\n"
                    "const apiKey = 'sk-abc123xyz789';\n"
                    "const dbPassword = 'admin123';"
                ),
                "expected": (
                    "Flag hardcoded credentials as a critical security issue, recommend storing secrets "
                    "in environment variables, explain the risk of committing secrets to version control."
                ),
                "criteria": (
                    "Identifies hardcoded credentials as critical, recommends environment variables "
                    "or a secrets manager, explains why."
                ),
            },
            {
                "input": (
                    "Review this Python function:\n\n"
                    "def find_duplicates(lst):\n"
                    "    duplicates = []\n"
                    "    for i in range(len(lst)):\n"
                    "        for j in range(len(lst)):\n"
                    "            if i != j and lst[i] == lst[j]:\n"
                    "                if lst[i] not in duplicates:\n"
                    "                    duplicates.append(lst[i])\n"
                    "    return duplicates"
                ),
                "expected": (
                    "Identify the O(n³) time complexity, suggest an efficient O(n) solution "
                    "using a Counter or set, and provide a corrected implementation."
                ),
                "criteria": (
                    "Correctly identifies the high complexity, proposes a significantly more "
                    "efficient approach, provides working example code."
                ),
            },
            {
                "input": (
                    "Review this Python function:\n\n"
                    "def divide(a, b):\n"
                    "    return a / b"
                ),
                "expected": (
                    "Flag the missing division-by-zero guard. Suggest a try/except block "
                    "or a conditional check before dividing."
                ),
                "criteria": "Identifies the missing ZeroDivisionError handling, provides a corrected version.",
            },
            {
                "input": (
                    "Review this Python code:\n\n"
                    "if username == None:\n"
                    "    return False"
                ),
                "expected": (
                    "Flag the incorrect None comparison using ==. Recommend 'if username is None:' "
                    "per PEP 8, or 'if not username:' for falsy checks."
                ),
                "criteria": "Identifies the incorrect equality comparison with None, explains the Pythonic 'is None' alternative.",
            },
            {
                "input": (
                    "Review this Python function:\n\n"
                    "def read_config():\n"
                    "    return open('config.json').read()"
                ),
                "expected": (
                    "Flag the unclosed file handle (resource leak). Recommend using a 'with' "
                    "context manager to ensure the file is always closed."
                ),
                "criteria": "Identifies the resource leak from an unclosed file, recommends 'with open(...) as f:' pattern.",
            },
            {
                "input": (
                    "Review this Python:\n\n"
                    "for i in range(len(items)):\n"
                    "    process(items[i])"
                ),
                "expected": (
                    "Suggest using direct iteration 'for item in items:' as the Pythonic alternative, "
                    "and explain why it's cleaner."
                ),
                "criteria": "Identifies the non-idiomatic pattern, recommends direct iteration, brief explanation.",
            },
            {
                "input": (
                    "Review this React useEffect:\n\n"
                    "useEffect(() => {\n"
                    "  fetch('/api/data')\n"
                    "    .then(r => r.json())\n"
                    "    .then(setData)\n"
                    "}, [])"
                ),
                "expected": (
                    "Point out the missing cleanup: no AbortController or cancelled flag, which can cause "
                    "setState on an unmounted component. Suggest AbortController for cleanup."
                ),
                "criteria": (
                    "Identifies the potential setState-on-unmounted-component issue, "
                    "recommends an AbortController or isMounted flag."
                ),
            },
        ],
    },
    {
        "name": "Factual Q&A",
        "description": (
            "Tests factual recall accuracy on geography, science, history, and technology questions."
        ),
        "cases": [
            {
                "input": "What is the capital of Australia?",
                "expected": "Canberra",
                "criteria": "Correct answer (Canberra, not Sydney or Melbourne). Concise and unambiguous.",
            },
            {
                "input": "What is the speed of light in a vacuum?",
                "expected": "Approximately 299,792,458 meters per second (roughly 3×10⁸ m/s or 186,282 miles per second).",
                "criteria": "Numerically accurate with appropriate units. Rounded value with explanation is acceptable.",
            },
            {
                "input": "In what year did World War II end?",
                "expected": "1945. VE Day (Victory in Europe) was May 8, 1945; VJ Day (Victory over Japan) was September 2, 1945.",
                "criteria": "Correct year (1945). Including both European and Pacific end dates earns full marks.",
            },
            {
                "input": "What does CPU stand for?",
                "expected": "Central Processing Unit",
                "criteria": "Correct full expansion. Brief description of what a CPU does is acceptable but not required.",
            },
            {
                "input": "What is the largest planet in our solar system?",
                "expected": "Jupiter",
                "criteria": "Correct planet name. Factually accurate without hedging.",
            },
            {
                "input": "What is the Pythagorean theorem?",
                "expected": (
                    "In a right triangle, the square of the hypotenuse equals the sum of the squares "
                    "of the other two sides: a² + b² = c², where c is the hypotenuse."
                ),
                "criteria": "Correct mathematical statement with the formula. Clear identification of which side is the hypotenuse.",
            },
            {
                "input": "Who wrote Pride and Prejudice?",
                "expected": "Jane Austen. It was published in 1813.",
                "criteria": "Correct author attribution. Publication year is a bonus but not required.",
            },
            {
                "input": "What programming language is the Linux kernel primarily written in?",
                "expected": "C, with a small amount of assembly language.",
                "criteria": "Correct primary language (C). Mention of assembly is accurate and acceptable.",
            },
        ],
    },
]

MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]


async def seed_suites() -> list[int]:
    """Create suites and cases if they don't exist. Returns suite IDs in SUITES order."""
    suite_ids = []
    async with AsyncSessionLocal() as db:
        for suite_data in SUITES:
            result = await db.execute(
                select(TestSuite).where(TestSuite.name == suite_data["name"])
            )
            suite = result.scalar_one_or_none()
            if suite:
                print(f"  skip (exists): {suite.name}  id={suite.id}")
                suite_ids.append(suite.id)
                continue

            suite = TestSuite(name=suite_data["name"], description=suite_data["description"])
            db.add(suite)
            await db.flush()

            for case_data in suite_data["cases"]:
                db.add(TestCase(suite_id=suite.id, **case_data))

            await db.commit()
            print(f"  created: {suite.name}  id={suite.id}  ({len(suite_data['cases'])} cases)")
            suite_ids.append(suite.id)

    return suite_ids


async def seed_runs(suite_ids: list[int]) -> None:
    """For each suite+model pair, create and execute a run if one doesn't already exist."""
    for suite_id, suite_data in zip(suite_ids, SUITES):
        for model in MODELS:
            async with AsyncSessionLocal() as db:
                existing = await db.execute(
                    select(Run).where(
                        Run.suite_id == suite_id,
                        Run.model_name == model,
                        Run.status == "completed",
                    )
                )
                if existing.scalar_one_or_none():
                    print(f"  skip (exists): suite={suite_id} model={model}")
                    continue

                run = Run(suite_id=suite_id, model_name=model, status="pending")
                db.add(run)
                await db.commit()
                await db.refresh(run)

            run_id = run.id
            print(f"  running: suite={suite_id} ({suite_data['name']})  model={model}  run_id={run_id}")

            async def noop(event: dict) -> None:
                pass

            async with AsyncSessionLocal() as db:
                await execute_run(run_id, db, noop)

            print(f"  done:    run_id={run_id}")


async def main() -> None:
    print("--- suites and test cases ---")
    suite_ids = await seed_suites()

    print("\n--- runs (calls Groq — takes a few minutes) ---")
    await seed_runs(suite_ids)

    print("\ndone.")


if __name__ == "__main__":
    asyncio.run(main())
