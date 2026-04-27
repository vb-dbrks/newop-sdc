"""SQLAlchemy ORM models — first-screen subset of the v2 schema.

See `velocia/design-specs/architecture/02-data-model.md` for the full v2 model
and `adr/0021-defer-alembic.md` for why these are auto-created on app startup
via `Base.metadata.create_all(engine)` rather than via Alembic.

Tables defined here (Phase 1):
  - users
  - study_documents          (umbrella; body tables come with their endpoints)
  - study_access_list        (per-study Author/Reviewer roles)
  - audit_log                (append-only field-level history)
  - agent_runs               (mirror of every AI invocation)
  - idempotency_keys         (request-level idempotency cache)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.domain.enums import (
    AgentRunKind,
    AgentRunStatus,
    AuditAction,
    DocumentType,
    StudyAccessRole,
    StudyStatus,
)
from backend.settings import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    All tables are pinned to `settings.db_schema` (e.g. `velocia` on
    Lakebase). When unset (SQLite local dev / tests) tables live in the
    default schema as before.
    """

    metadata = MetaData(schema=settings.db_schema)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    sso_subject: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ex_prid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    onboarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    access_grants: Mapped[list[StudyAccessList]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="StudyAccessList.user_id",
    )


class StudyDocument(Base):
    __tablename__ = "study_documents"

    study_document_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    document_type: Mapped[DocumentType] = mapped_column(String(32), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    study_brief_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    study_acronym: Mapped[str | None] = mapped_column(String(64), nullable=True)
    study_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    study_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    study_status: Mapped[StudyStatus] = mapped_column(
        String(32), nullable=False, default=StudyStatus.DRAFT.value, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_modified_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=True
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reviewed_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    access_list: Mapped[list[StudyAccessList]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    audit_entries: Mapped[list[AuditLog]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(back_populates="document")

    __table_args__ = (
        Index(
            "ix_study_documents_type_status",
            "document_type",
            "study_status",
        ),
    )


class StudyAccessList(Base):
    __tablename__ = "study_access_list"

    study_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study_documents.study_document_id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), primary_key=True
    )
    role: Mapped[StudyAccessRole] = mapped_column(String(16), primary_key=True)

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    granted_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=False
    )
    expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    document: Mapped[StudyDocument] = relationship(back_populates="access_list")
    user: Mapped[User] = relationship(back_populates="access_grants", foreign_keys=[user_id])


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    study_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study_documents.study_document_id"), nullable=False, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=True
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[AuditAction] = mapped_column(String(32), nullable=False)
    value_before: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    supervisor_agent_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[StudyDocument] = relationship(back_populates="audit_entries")

    __table_args__ = (
        Index(
            "ix_audit_log_doc_field_time",
            "study_document_id",
            "field_name",
            "timestamp",
        ),
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    agent_run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    study_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("study_documents.study_document_id"), nullable=True, index=True
    )
    run_kind: Mapped[AgentRunKind] = mapped_column(String(32), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    triggered_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=False
    )
    external_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[AgentRunStatus] = mapped_column(String(32), nullable=False, index=True)
    step_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[StudyDocument | None] = relationship(back_populates="agent_runs")


class IdempotencyKey(Base):
    """Request-level idempotency cache. See backend/middleware/idempotency.py."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.user_id"), primary_key=True
    )
    response_body: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


__all__ = [
    "AgentRun",
    "AuditLog",
    "Base",
    "IdempotencyKey",
    "StudyAccessList",
    "StudyDocument",
    "User",
]
