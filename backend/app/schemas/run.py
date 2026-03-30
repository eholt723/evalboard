from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    suite_id: int
    model_name: str
    prompt_variant_id: int | None = None


class RunResultOut(BaseModel):
    id: int
    run_id: int
    test_case_id: int
    response_text: str | None
    score: int | None
    pass_: bool | None
    strengths: list[str] | None
    weaknesses: list[str] | None
    reasoning: str | None
    latency_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class RunSummaryOut(BaseModel):
    run_id: int
    avg_score: float | None
    pass_rate: float | None
    total_cases: int
    completed_cases: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: int
    suite_id: int
    model_name: str
    prompt_variant_id: int | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    summary: RunSummaryOut | None = None

    model_config = {"from_attributes": True}


class RunDetail(RunOut):
    results: list[RunResultOut] = []
