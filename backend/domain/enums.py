from enum import StrEnum


class DocumentType(StrEnum):
    NEW_OPPORTUNITY = "new_opportunity"
    SDC = "sdc"
    PROTOCOL = "protocol"


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"


class StudyRole(StrEnum):
    AUTHOR = "author"
    REVIEWER = "reviewer"


class FieldType(StrEnum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX_GROUP = "checkbox_group"
    NUMBER = "number"


class ValueOrigin(StrEnum):
    AGENT_GENERATED = "agent_generated"
    AGENT_ENHANCED = "agent_enhanced"
    USER_EDIT = "user_edit"
    USER_INITIAL = "user_initial"


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


class IngestionStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    INDEXED = "indexed"
    FAILED = "failed"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ThreadStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class NotificationKind(StrEnum):
    REVIEW_REQUESTED = "review_requested"
    COMMENT_ADDED = "comment_added"
    APPROVAL_DECIDED = "approval_decided"
    DOCUMENT_APPROVED = "document_approved"
    AGENT_RUN_FAILED = "agent_run_failed"
    FILE_INDEXED = "file_indexed"
