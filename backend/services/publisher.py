"""Publish-on-approval projection from Velocia authoring layer to IA Clinical Study Domain.

Triggered when a Protocol document advances to `Approved` (see ADR 0017 and
06-sequence-review-approve.md). Reads the latest non-superseded field values
from `document_field_values` and projects them onto:
  - clinical_study (UPDATE — set indication_id, therapeutic_area_medical_id,
    study_type_id, study_phase_type_id, study_status_type_id, alliance_id,
    product_family_id, primary_objective, secondary_objective,
    published_from_document_id)
  - study_arm (UPSERT from the document's `study_arms` repeating-section field)
  - eligibility_criteria (UPSERT from the `eligibility_criteria` field)

Runs in the same transaction as the document status flip — atomic publish.
"""

from uuid import UUID


async def publish_protocol(*, document_id: UUID, version_id: UUID, actor_user_id: UUID) -> None:
    """Project an approved Protocol document onto the canonical clinical_study row.

    Pre-conditions:
      - document.type == 'protocol'
      - document.status == 'in_review' (we run inside the approve transaction
        before the flip to 'approved' completes)
      - All assigned Reviewers have decision='approved' for `version_id`.

    Side effects (within the caller's transaction):
      - UPDATE clinical_study SET <projected fields>, published_from_document_id=version_id
      - UPSERT study_arm rows
      - UPSERT eligibility_criteria rows
      - INSERT audit_log (action='published_to_clinical_study')
    """
    raise NotImplementedError(
        "TODO: load latest field values via repositories/fields, look up reference IDs "
        "(indication, therapeutic_area_medical, study_type, study_phase_type, etc.), "
        "and apply the projection. See backend/domain/templates/sdc.v1.yaml for the "
        "field → canonical-column mapping."
    )
