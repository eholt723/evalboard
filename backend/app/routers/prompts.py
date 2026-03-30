from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.prompt import PromptVariant
from app.schemas.prompt import PromptVariantCreate, PromptVariantOut

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptVariantOut])
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptVariant).order_by(PromptVariant.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=PromptVariantOut, status_code=201)
async def create_prompt(payload: PromptVariantCreate, db: AsyncSession = Depends(get_db)):
    # auto-increment version for same name
    result = await db.execute(
        select(PromptVariant)
        .where(PromptVariant.name == payload.name)
        .order_by(PromptVariant.version.desc())
    )
    latest = result.scalars().first()
    version = (latest.version + 1) if latest else 1

    variant = PromptVariant(**payload.model_dump(), version=version)
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


@router.get("/{prompt_id}", response_model=PromptVariantOut)
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptVariant).where(PromptVariant.id == prompt_id))
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Prompt variant not found")
    return variant


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptVariant).where(PromptVariant.id == prompt_id))
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Prompt variant not found")
    await db.delete(variant)
    await db.commit()
