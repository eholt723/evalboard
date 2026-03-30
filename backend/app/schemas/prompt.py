from datetime import datetime
from pydantic import BaseModel


class PromptVariantBase(BaseModel):
    name: str
    system_prompt: str


class PromptVariantCreate(PromptVariantBase):
    pass


class PromptVariantOut(PromptVariantBase):
    id: int
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
