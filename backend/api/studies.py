"""Portfolio + study_document read endpoints.

Schema: study_document is the umbrella; new_opportunity / study_design_concept /
study_protocol are body tables. See ADR 0018 and 02-data-model.md.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.sso import CurrentUserRowDep
from backend.db.repositories import access_list as access_list_repo
from backend.db.session import get_session
from backend.domain.enums import DocumentType, StudyStatus
from backend.domain.models import StudyAccessList, StudyDocument, User
from backend.domain.schemas import StudyDocumentList, StudyDocumentSummary

router = APIRouter(prefix="/study-documents", tags=["study-documents"])


@router.get("", response_model=StudyDocumentList)
async def list_study_documents(
    user: CurrentUserRowDep,
    db: Annotated[AsyncSession, Depends(get_session)],
    document_type: DocumentType | None = None,
    study_status: StudyStatus | None = None,
    q: str | None = None,
):
    """Portfolio table — study_documents the caller has any active access to."""
    stmt = (
        select(StudyDocument, User.name.label("last_modified_by_name"))
        .join(
            StudyAccessList,
            StudyAccessList.study_document_id == StudyDocument.study_document_id,
        )
        .outerjoin(User, User.user_id == StudyDocument.last_modified_by)
        .where(
            StudyAccessList.user_id == user.user_id,
            StudyAccessList.is_active.is_(True),
            StudyDocument.deleted_at.is_(None),
        )
        .order_by(StudyDocument.last_modified_at.desc())
    )
    if document_type is not None:
        stmt = stmt.where(StudyDocument.document_type == document_type)
    if study_status is not None:
        stmt = stmt.where(StudyDocument.study_status == study_status)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            (StudyDocument.study_brief_title.ilike(like))
            | (StudyDocument.study_acronym.ilike(like))
            | (StudyDocument.study_id.ilike(like))
        )

    rows = (await db.execute(stmt)).all()
    items = [
        StudyDocumentSummary(
            study_document_id=doc.study_document_id,
            document_type=doc.document_type,
            study_status=doc.study_status,
            study_brief_title=doc.study_brief_title,
            study_acronym=doc.study_acronym,
            study_id=doc.study_id,
            last_modified_at=doc.last_modified_at,
            last_modified_by_name=name,
        )
        for doc, name in rows
    ]
    return StudyDocumentList(items=items, next_page=None)


@router.get("/{study_document_id}")
async def get_study_document(
    study_document_id: str,
    user: CurrentUserRowDep,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Single document. 404 if caller has no active access — see ADR 0019."""
    role = await access_list_repo.get_active_role(
        db, study_document_id=study_document_id, user_id=user.user_id
    )
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    doc = (
        await db.execute(
            select(StudyDocument).where(
                StudyDocument.study_document_id == study_document_id,
                StudyDocument.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {
        "study_document_id": doc.study_document_id,
        "document_type": doc.document_type,
        "study_status": doc.study_status,
        "study_brief_title": doc.study_brief_title,
        "study_acronym": doc.study_acronym,
        "study_id": doc.study_id,
        "current_version": doc.current_version,
        "last_modified_at": doc.last_modified_at.isoformat(),
        "your_role": role,
    }


@router.get("/{study_document_id}/versions")
async def list_versions(study_document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
