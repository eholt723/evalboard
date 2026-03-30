from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.suite import TestSuite
from app.models.case import TestCase
from app.schemas.suite import TestSuiteCreate, TestSuiteOut, TestSuiteDetail, TestCaseCreate, TestCaseOut

router = APIRouter(prefix="/suites", tags=["suites"])


@router.get("", response_model=list[TestSuiteOut])
async def list_suites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestSuite).order_by(TestSuite.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=TestSuiteOut, status_code=201)
async def create_suite(payload: TestSuiteCreate, db: AsyncSession = Depends(get_db)):
    suite = TestSuite(**payload.model_dump())
    db.add(suite)
    await db.commit()
    await db.refresh(suite)
    return suite


@router.get("/{suite_id}", response_model=TestSuiteDetail)
async def get_suite(suite_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestSuite)
        .where(TestSuite.id == suite_id)
        .options(selectinload(TestSuite.cases))
    )
    suite = result.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite


@router.delete("/{suite_id}", status_code=204)
async def delete_suite(suite_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
    suite = result.scalar_one_or_none()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    await db.delete(suite)
    await db.commit()


@router.post("/{suite_id}/cases", response_model=TestCaseOut, status_code=201)
async def add_case(suite_id: int, payload: TestCaseCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Suite not found")
    case = TestCase(suite_id=suite_id, **payload.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.delete("/{suite_id}/cases/{case_id}", status_code=204)
async def delete_case(suite_id: int, case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestCase).where(TestCase.id == case_id, TestCase.suite_id == suite_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    await db.delete(case)
    await db.commit()
