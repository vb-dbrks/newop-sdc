"""Pydantic request/response schemas for the API layer.

Phase-1 set: only the schemas we need for the endpoints we're wiring now
(/api/me, GET /api/study-documents). Others land alongside their endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.enums import (
    DocumentType,
    StudyAccessRole,
    StudyStatus,
)


class _ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MeResponse(_ApiModel):
    user_id: str
    sso_subject: str
    email: str
    name: str
    onboarded_at: datetime


class StudyDocumentSummary(_ApiModel):
    study_document_id: str
    document_type: DocumentType
    study_status: StudyStatus
    study_brief_title: str | None = None
    study_acronym: str | None = None
    study_id: str | None = None
    last_modified_at: datetime
    last_modified_by_name: str | None = None


class StudyDocumentList(BaseModel):
    items: list[StudyDocumentSummary]
    next_page: str | None = None


class GenerateRequest(BaseModel):
    document_type: DocumentType
    prompt: str = Field(min_length=1, max_length=10_000)
    parent_opportunity_id: str | None = None
    attached_source_document_ids: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    study_document_id: str
    agent_run_id: str


class AgentRunStatusResponse(BaseModel):
    agent_run_id: str
    status: str
    step_history: list[dict] = Field(default_factory=list)
    error_message: str | None = None
    study_document_id: str | None = None


class GrantAccessRequest(BaseModel):
    user_id: str
    role: StudyAccessRole
    expire_at: datetime | None = None
