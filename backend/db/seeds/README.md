# Reference data seeds (dev only)

Layer 3 of the data model — the IA Clinical Study reference / master data
(`indication`, `therapeutic_area_medical`, `study_type`, `study_phase_type`,
`study_status_type`, `arm_type`, `eligibility_criteria_type`, `product_family`,
`alliance`, `code_system`, `code_type`, `subject_area`).

In production these tables are populated by the IA / data-governance pipeline.
For local dev we ship minimal fixtures here so the app boots with sensible
dropdown options.

To be added: per-table YAML fixtures and an alembic data-migration that loads
them when `ENV=development`. See ADR 0017.
