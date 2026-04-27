"""ENUMs aligned with the IA Velocia Application Data Model (v2). See ADR 0018."""

from enum import StrEnum


class DocumentType(StrEnum):
    NEW_OPPORTUNITY = "new_opportunity"
    SDC = "sdc"
    PROTOCOL = "protocol"


class StudyStatus(StrEnum):
    """study_document.study_status — TBD with IA, assumed enum."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"


class StudyAccessRole(StrEnum):
    AUTHOR = "author"
    REVIEWER = "reviewer"


class CriteriaType(StrEnum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class SourceDocumentSourceType(StrEnum):
    USER_UPLOAD = "user_upload"
    REFERENCE = "reference"
    GENERATED = "generated"


class IngestionStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    INDEXED = "indexed"
    FAILED = "failed"


class CommentStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUBMIT = "submit"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    PUBLISH = "publish"
    ENHANCE = "enhance"
    REVERT = "revert"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class VersionTrigger(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    MANUAL = "manual"


class AgentRunKind(StrEnum):
    GENERATE = "generate"
    ENHANCE_FIELD = "enhance_field"
    SIMULATE = "simulate"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationKind(StrEnum):
    REVIEW_REQUESTED = "review_requested"
    COMMENT_ADDED = "comment_added"
    APPROVAL_DECIDED = "approval_decided"
    DOCUMENT_APPROVED = "document_approved"
    AGENT_RUN_FAILED = "agent_run_failed"
    FILE_INDEXED = "file_indexed"
