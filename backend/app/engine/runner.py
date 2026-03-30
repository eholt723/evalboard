import asyncio
import time
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from typing import Any

from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.judge import judge_response
from app.models.case import TestCase
from app.models.prompt import PromptVariant
from app.models.run import Run, RunResult, RunSummary

CONCURRENCY = 5  # max parallel Groq inference calls per run

Publish = Callable[[dict], Coroutine[Any, Any, None]]


async def execute_run(run_id: int, db: AsyncSession, publish: Publish) -> None:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one()

    cases_result = await db.execute(
        select(TestCase).where(TestCase.suite_id == run.suite_id).order_by(TestCase.id)
    )
    cases = cases_result.scalars().all()

    system_prompt = None
    if run.prompt_variant_id:
        pv_result = await db.execute(
            select(PromptVariant).where(PromptVariant.id == run.prompt_variant_id)
        )
        pv = pv_result.scalar_one_or_none()
        system_prompt = pv.system_prompt if pv else None

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    await db.commit()

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def run_single_case(case: TestCase, index: int) -> None:
        async with semaphore:
            client = AsyncGroq(api_key=settings.groq_api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": case.input})

            start = time.monotonic()
            try:
                completion = await client.chat.completions.create(
                    model=run.model_name,
                    messages=messages,
                    temperature=0.7,
                )
                response_text = completion.choices[0].message.content
                latency_ms = int((time.monotonic() - start) * 1000)

                judgment = await judge_response(
                    input=case.input,
                    expected=case.expected,
                    criteria=case.criteria,
                    response=response_text,
                )
            except Exception as exc:
                response_text = None
                latency_ms = int((time.monotonic() - start) * 1000)
                judgment = {
                    "score": 0,
                    "pass": False,
                    "strengths": [],
                    "weaknesses": [str(exc)],
                    "reasoning": f"Error during inference or judging: {exc}",
                }

            run_result = RunResult(
                run_id=run_id,
                test_case_id=case.id,
                response_text=response_text,
                score=judgment["score"],
                pass_=judgment["pass"],
                strengths=judgment.get("strengths", []),
                weaknesses=judgment.get("weaknesses", []),
                reasoning=judgment.get("reasoning", ""),
                latency_ms=latency_ms,
            )
            db.add(run_result)
            await db.commit()
            await db.refresh(run_result)

            await publish({
                "type": "result",
                "index": index,
                "total": len(cases),
                "test_case_id": case.id,
                "run_result_id": run_result.id,
                "score": judgment["score"],
                "pass": judgment["pass"],
                "latency_ms": latency_ms,
            })

    await asyncio.gather(*[run_single_case(case, i + 1) for i, case in enumerate(cases)])

    results_query = await db.execute(
        select(RunResult).where(RunResult.run_id == run_id)
    )
    all_results = results_query.scalars().all()
    scored = [r for r in all_results if r.score is not None]
    avg_score = sum(r.score for r in scored) / len(scored) if scored else None
    passed = sum(1 for r in scored if r.pass_)
    pass_rate = passed / len(scored) if scored else None

    summary = RunSummary(
        run_id=run_id,
        avg_score=avg_score,
        pass_rate=pass_rate,
        total_cases=len(cases),
        completed_cases=len(scored),
    )
    db.add(summary)

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    await db.commit()

    await publish({
        "type": "complete",
        "avg_score": avg_score,
        "pass_rate": pass_rate,
        "total_cases": len(cases),
        "completed_cases": len(scored),
    })
