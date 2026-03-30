import json
import re
from groq import AsyncGroq

from app.config import settings

JUDGE_MODEL = "llama-3.3-70b-versatile"
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
    )
    raw = completion.choices[0].message.content.strip()

    # strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
