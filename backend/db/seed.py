"""Idempotent dev seed.

Single source of truth for the dev fixture (1 user + 5 study_documents +
5 author-role access grants). Used by:

  - backend.main.lifespan() — when SEED_ON_STARTUP=true, seeds inside the
    app process so a fresh deploy needs zero manual SQL or python steps.
  - scripts/seed_dev.py — for ad-hoc reruns from a workstation.

All inserts use SELECT-then-INSERT against deterministic uuid5 PKs, so
re-running is a no-op and the function works on both Postgres and
SQLite (used in local-dev / tests).
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.enums import DocumentType, StudyAccessRole, StudyStatus
from backend.domain.models import StudyAccessList, StudyDocument, User

logger = logging.getLogger(__name__)


# (study_brief_title, study_acronym, study_id, document_type, study_status)
_SEED_STUDIES: list[tuple[str, str, str, DocumentType, StudyStatus]] = [
    (
        "Tocavalumab in Moderate-to-Severe COPD with Frequent Exacerbations",
        "TOCA-COPD",
        "D9999C00001",
        DocumentType.NEW_OPPORTUNITY,
        StudyStatus.DRAFT,
    ),
    (
        "Tezepelumab Adolescent Airway Remodeling Substudy",
        "TEZ-AAR",
        "D9999C00002",
        DocumentType.NEW_OPPORTUNITY,
        StudyStatus.DRAFT,
    ),
    (
        "Endometriosis Symptom Profiler — Real-World Evidence Cohort",
        "ENDO-PROFILE",
        "D9999C00003",
        DocumentType.NEW_OPPORTUNITY,
        StudyStatus.DRAFT,
    ),
    (
        "Saxenda Cardiometabolic Phase IIb",
        "SAX-CARD-2B",
        "D9999C00004",
        DocumentType.SDC,
        StudyStatus.IN_REVIEW,
    ),
    (
        "Imfinzi NSCLC Adjuvant Phase III",
        "IMF-ADJ-3",
        "D9999C00005",
        DocumentType.SDC,
        StudyStatus.APPROVED,
    ),
]


def _stable_uuid(seed: str) -> str:
    """Deterministic UUID5 so reruns stay idempotent."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"velocia-seed:{seed}"))


async def seed_default(
    session: AsyncSession, *, user_email: str, user_name: str
) -> dict[str, int]:
    """Insert (or refresh) the dev fixture. Returns insert counts.

    Idempotent: deterministic primary keys + select-before-insert so calling
    repeatedly is safe. Only the user's display name is updated on each run;
    other fields are not touched once they exist.
    """
    counts = {"users": 0, "study_documents": 0, "study_access_list": 0}

    # User
    existing_user = (
        await session.execute(select(User).where(User.sso_subject == user_email))
    ).scalar_one_or_none()
    if existing_user is None:
        user = User(
            user_id=_stable_uuid(user_email),
            sso_subject=user_email,
            email=user_email,
            name=user_name,
        )
        session.add(user)
        await session.flush()
        counts["users"] = 1
    else:
        user = existing_user
        if existing_user.name != user_name:
            existing_user.name = user_name

    # Studies + access grants
    for title, acronym, study_id, doc_type, status in _SEED_STUDIES:
        sd_id = _stable_uuid(study_id)
        sd_existing = (
            await session.execute(
                select(StudyDocument).where(StudyDocument.study_document_id == sd_id)
            )
        ).scalar_one_or_none()
        if sd_existing is None:
            session.add(
                StudyDocument(
                    study_document_id=sd_id,
                    document_type=doc_type,
                    study_brief_title=title,
                    study_acronym=acronym,
                    study_id=study_id,
                    study_status=status,
                    last_modified_by=user.user_id,
                    current_version=1,
                )
            )
            counts["study_documents"] += 1

        access_existing = (
            await session.execute(
                select(StudyAccessList).where(
                    StudyAccessList.study_document_id == sd_id,
                    StudyAccessList.user_id == user.user_id,
                    StudyAccessList.role == StudyAccessRole.AUTHOR,
                )
            )
        ).scalar_one_or_none()
        if access_existing is None:
            session.add(
                StudyAccessList(
                    study_document_id=sd_id,
                    user_id=user.user_id,
                    role=StudyAccessRole.AUTHOR,
                    granted_by=user.user_id,
                    is_active=True,
                )
            )
            counts["study_access_list"] += 1

    await session.commit()
    logger.info("Dev seed applied: %s", counts)
    return counts
