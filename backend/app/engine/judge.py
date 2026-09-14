import json
import re
from groq import AsyncGroq

from app.config import settings

JUDGE_MODEL = "openai/gpt-oss-120b"
JUDGE_TEMPERATURE = 0.1

JUDGE_PROMPT = """\
You are an LLM output evaluator. Score the following response objectively.

Input: {input}
Expected: {expected}
Criteria: {criteria}
Actual response: {response}

Return ONLY valid JSON with this exact structure:
{{
  "score": <integer 1-10>,
  "pass": <true if score >= 7 else false>,
  "strengths": [<string>, ...],
  "weaknesses": [<string>, ...],
  "reasoning": "<one to three sentences explaining the score>"
}}"""


class JudgeParseError(ValueError):
    """Raised when the judge model's output can't be parsed as the expected JSON schema."""


async def judge_response(input: str, expected: str, criteria: str, response: str) -> dict:
    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = JUDGE_PROMPT.format(
        input=input,
        expected=expected,
        criteria=criteria,
        response=response,
    )
    completion = await client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=JUDGE_TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort="low",
        include_reasoning=False,
    )
    raw = completion.choices[0].message.content.strip()

    # gpt-oss sometimes wraps the JSON in commentary or code fences despite the
    # "return ONLY valid JSON" instruction — pull out the outermost {...} object
    # rather than assuming the whole trimmed string is valid JSON.
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise JudgeParseError(f"Judge response contained no JSON object: {raw[:200]!r}")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise JudgeParseError(f"Judge response was not valid JSON: {exc}") from exc

    if "score" not in parsed:
        raise JudgeParseError(f"Judge response missing required 'score' field: {parsed!r}")

    return {
        "score": parsed["score"],
        "pass": bool(parsed.get("pass", False)),
        "strengths": parsed.get("strengths", []),
        "weaknesses": parsed.get("weaknesses", []),
        "reasoning": parsed.get("reasoning", ""),
    }
