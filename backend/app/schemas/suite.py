from datetime import datetime
from pydantic import BaseModel


class TestCaseBase(BaseModel):
    input: str
    expected: str
    criteria: str


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseOut(TestCaseBase):
    id: int
    suite_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TestSuiteBase(BaseModel):
    name: str
    description: str | None = None


class TestSuiteCreate(TestSuiteBase):
    pass


class TestSuiteOut(TestSuiteBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TestSuiteDetail(TestSuiteOut):
    cases: list[TestCaseOut] = []
