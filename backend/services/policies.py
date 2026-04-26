"""Approval-policy evaluator.

Implements ADR 0006: a document advances to Approved only when every Reviewer
in the version's frozen review pool has decided 'approved' for that version.
"""

from uuid import UUID


async def has_unanimous_approval(*, document_id: UUID, version_id: UUID) -> bool:
    raise NotImplementedError(
        "TODO: COUNT(approved decisions for version_id) == COUNT(reviewers in pool for version_id)"
    )
