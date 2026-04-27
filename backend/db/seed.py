"""Idempotent dev seed.

Single source of truth for the dev fixture (N users + 5 study_documents +
per-user access grants). Used by:

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


def _coerce_role(role: str | StudyAccessRole) -> StudyAccessRole:
    if isinstance(role, StudyAccessRole):
        return role
    try:
        return StudyAccessRole(role)
    except ValueError as e:
        raise ValueError(
            f"Unknown role {role!r}; expected one of "
            f"{[r.value for r in StudyAccessRole]}"
        ) from e


async def _upsert_user(
    session: AsyncSession, *, email: str, name: str
) -> tuple[User, bool]:
    """Insert the user row if missing; refresh display name if it drifted.

    Returns (User, inserted_now).
    """
    existing = (
        await session.execute(select(User).where(User.sso_subject == email))
    ).scalar_one_or_none()
    if existing is None:
        user = User(
            user_id=_stable_uuid(email),
            sso_subject=email,
            email=email,
            name=name,
        )
        session.add(user)
        await session.flush()
        return user, True
    if existing.name != name:
        existing.name = name
    return existing, False


async def _ensure_study(
    session: AsyncSession,
    *,
    title: str,
    acronym: str,
    study_id: str,
    doc_type: DocumentType,
    status: StudyStatus,
    last_modified_by: str,
) -> tuple[str, bool]:
    """Insert the study_document if missing. Returns (sd_id, inserted_now)."""
    sd_id = _stable_uuid(study_id)
    existing = (
        await session.execute(
            select(StudyDocument).where(StudyDocument.study_document_id == sd_id)
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            StudyDocument(
                study_document_id=sd_id,
                document_type=doc_type,
                study_brief_title=title,
                study_acronym=acronym,
                study_id=study_id,
                study_status=status,
                last_modified_by=last_modified_by,
                current_version=1,
            )
        )
        return sd_id, True
    return sd_id, False


async def _grant_access(
    session: AsyncSession,
    *,
    study_document_id: str,
    user_id: str,
    role: StudyAccessRole,
    granted_by: str,
) -> bool:
    """Add an access_list row if (study, user, role) doesn't already exist."""
    existing = (
        await session.execute(
            select(StudyAccessList).where(
                StudyAccessList.study_document_id == study_document_id,
                StudyAccessList.user_id == user_id,
                StudyAccessList.role == role,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    session.add(
        StudyAccessList(
            study_document_id=study_document_id,
            user_id=user_id,
            role=role,
            granted_by=granted_by,
            is_active=True,
        )
    )
    return True


async def seed_users(
    session: AsyncSession, users: list[dict]
) -> dict[str, int]:
    """Seed multiple users + the shared 5-study fixture + per-user grants.

    Each entry in `users` is::

        {
            "email":   "<sso subject / email>",
            "name":    "<display name>",
            "role":    "author" | "reviewer",        # default: "author"
            "studies": ["D9999C00001", ...] | None,  # default: all 5
        }

    `studies` controls which of the 5 fixture studies a user gets access
    to — `None` means all five. Useful for verifying the per-study
    authorization model: e.g. seed alice with studies=["D9999C00001"] and
    bob with studies=["D9999C00002"], then log in as each and check the
    portfolio table is correctly scoped.

    Idempotent end-to-end. Returns insert counts.
    """
    if not users:
        return {"users": 0, "study_documents": 0, "study_access_list": 0}

    counts = {"users": 0, "study_documents": 0, "study_access_list": 0}

    # 1. Upsert users.
    user_rows: dict[str, tuple[User, StudyAccessRole, set[str] | None]] = {}
    for spec in users:
        email = spec["email"]
        name = spec.get("name") or email
        role = _coerce_role(spec.get("role", StudyAccessRole.AUTHOR))
        studies = spec.get("studies")
        if studies is not None:
            studies = set(studies)

        user, inserted = await _upsert_user(session, email=email, name=name)
        if inserted:
            counts["users"] += 1
        user_rows[email] = (user, role, studies)

    # 2. Use the *first* user as the `last_modified_by` for any new studies.
    primary_user = next(iter(user_rows.values()))[0]

    # 3. Insert studies if missing.
    sd_ids: dict[str, str] = {}
    for title, acronym, study_id, doc_type, status in _SEED_STUDIES:
        sd_id, inserted = await _ensure_study(
            session,
            title=title,
            acronym=acronym,
            study_id=study_id,
            doc_type=doc_type,
            status=status,
            last_modified_by=primary_user.user_id,
        )
        sd_ids[study_id] = sd_id
        if inserted:
            counts["study_documents"] += 1

    # 4. Per-user access grants.
    for _email, (user, role, studies) in user_rows.items():
        for study_id, sd_id in sd_ids.items():
            if studies is not None and study_id not in studies:
                continue
            granted = await _grant_access(
                session,
                study_document_id=sd_id,
                user_id=user.user_id,
                role=role,
                granted_by=primary_user.user_id,
            )
            if granted:
                counts["study_access_list"] += 1

    await session.commit()
    logger.info("Dev seed applied: %s users=%s", counts, list(user_rows))
    return counts


async def seed_default(
    session: AsyncSession, *, user_email: str, user_name: str
) -> dict[str, int]:
    """Single-user convenience wrapper around `seed_users`. Backward compat."""
    return await seed_users(
        session,
        users=[
            {
                "email": user_email,
                "name": user_name,
                "role": StudyAccessRole.AUTHOR,
            }
        ],
    )
