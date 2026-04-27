-- Velocia — Lakebase Postgres bootstrap + seed (alternative to scripts/seed_dev.py).
--
-- Use this when running scripts/seed_dev.py from your laptop is blocked by
-- network/firewall (e.g. WSAETIMEDOUT on Windows). It is fully self-contained:
-- creates the schema, optionally grants the app's service principal access to
-- it, and inserts the same dev fixture (1 user + 5 study_documents + 5
-- study_access_list rows).
--
-- ============================================================================
-- HOW TO RUN
-- ============================================================================
-- 1. In the Databricks workspace UI: SQL Editor (or a notebook with a Postgres
--    cursor), connect to the Lakebase instance (e.g. velocia-newop-sdc-db,
--    database `databricks_postgres`) — networking is internal so timeouts go
--    away.
--
-- 2. Edit the 3 placeholders in the BEFORE-YOU-RUN block below:
--      :seed_user_email   — your Databricks/SCIM email
--      :seed_user_name    — display name in the UI
--      :app_sp_client_id  — the velocia app's service principal client_id
--                           (grab from `databricks apps get velocia-newop-sdc`
--                           field `service_principal_client_id`).
--
-- 3. Execute top-to-bottom. Re-running is safe — every INSERT uses
--    ON CONFLICT DO NOTHING and DDL uses IF NOT EXISTS.
--
-- ============================================================================
-- BEFORE YOU RUN — replace these three values with literals.
-- (Lakebase runs Postgres but the Databricks SQL editor doesn't always support
--  psql ":var" substitution; safest is to find/replace the 3 placeholders.)
-- ============================================================================
--   <SEED_USER_EMAIL>    e.g. 'alice@customer.com'
--   <SEED_USER_NAME>     e.g. 'Alice Customer'
--   <APP_SP_CLIENT_ID>   e.g. '7d3b2a14-8b0a-4f9b-9b13-1a2f3c4d5e6f'
--                        (omit / comment out the GRANT block if you don't
--                         have it yet — the app's lifespan() can no-op if the
--                         schema already exists.)
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Schema (mirrors backend/domain/models.py — Phase-1 subset)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    user_id        VARCHAR(36)  PRIMARY KEY,
    sso_subject    VARCHAR(320) NOT NULL UNIQUE,
    email          VARCHAR(320) NOT NULL,
    name           VARCHAR(255) NOT NULL,
    ex_prid        VARCHAR(64),
    onboarded_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_sso_subject ON users (sso_subject);

CREATE TABLE IF NOT EXISTS study_documents (
    study_document_id   VARCHAR(36)  PRIMARY KEY,
    document_type       VARCHAR(32)  NOT NULL,
    project_id          VARCHAR(64),
    study_brief_title   VARCHAR(512),
    study_acronym       VARCHAR(64),
    study_id            VARCHAR(64),
    study_type          VARCHAR(64),
    study_status        VARCHAR(32)  NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_modified_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_modified_by    VARCHAR(36)  REFERENCES users(user_id),
    current_version     INTEGER      NOT NULL DEFAULT 1,
    reviewed_by         VARCHAR(36)  REFERENCES users(user_id),
    deleted_at          TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_study_documents_study_id
    ON study_documents (study_id);
CREATE INDEX IF NOT EXISTS ix_study_documents_study_status
    ON study_documents (study_status);
CREATE INDEX IF NOT EXISTS ix_study_documents_type_status
    ON study_documents (document_type, study_status);

CREATE TABLE IF NOT EXISTS study_access_list (
    study_document_id   VARCHAR(36)  NOT NULL REFERENCES study_documents(study_document_id),
    user_id             VARCHAR(36)  NOT NULL REFERENCES users(user_id),
    role                VARCHAR(16)  NOT NULL,
    granted_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    granted_by          VARCHAR(36)  NOT NULL REFERENCES users(user_id),
    expire_at           TIMESTAMPTZ,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    PRIMARY KEY (study_document_id, user_id, role)
);
CREATE INDEX IF NOT EXISTS ix_study_access_list_is_active
    ON study_access_list (is_active);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id                       VARCHAR(36)  PRIMARY KEY,
    study_document_id            VARCHAR(36)  NOT NULL REFERENCES study_documents(study_document_id),
    user_id                      VARCHAR(36)  REFERENCES users(user_id),
    field_name                   VARCHAR(255) NOT NULL,
    action                       VARCHAR(32)  NOT NULL,
    value_before                 TEXT,
    value_after                  TEXT,
    timestamp                    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    supervisor_agent_endpoint    VARCHAR(512),
    session_id                   VARCHAR(64),
    trace_id                     VARCHAR(64),
    signature                    TEXT
);
CREATE INDEX IF NOT EXISTS ix_audit_log_doc
    ON audit_log (study_document_id);
CREATE INDEX IF NOT EXISTS ix_audit_log_doc_field_time
    ON audit_log (study_document_id, field_name, timestamp);

CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id           VARCHAR(36)  PRIMARY KEY,
    study_document_id      VARCHAR(36)  REFERENCES study_documents(study_document_id),
    run_kind               VARCHAR(32)  NOT NULL,
    field_name             VARCHAR(255),
    triggered_by_user_id   VARCHAR(36)  NOT NULL REFERENCES users(user_id),
    external_run_id        VARCHAR(255),
    status                 VARCHAR(32)  NOT NULL,
    step_history           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    request_payload        JSONB        NOT NULL,
    response_payload       JSONB,
    error_message          TEXT,
    started_at             TIMESTAMPTZ,
    completed_at           TIMESTAMPTZ,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agent_runs_doc       ON agent_runs (study_document_id);
CREATE INDEX IF NOT EXISTS ix_agent_runs_status    ON agent_runs (status);
CREATE INDEX IF NOT EXISTS ix_agent_runs_external  ON agent_runs (external_run_id);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key               VARCHAR(255) NOT NULL,
    user_id           VARCHAR(36)  NOT NULL REFERENCES users(user_id),
    response_body     JSONB        NOT NULL,
    response_status   INTEGER      NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (key, user_id)
);
CREATE INDEX IF NOT EXISTS ix_idempotency_keys_created_at
    ON idempotency_keys (created_at);


-- ----------------------------------------------------------------------------
-- 2. Grant the app's service principal write access on schema public.
--
-- Lakebase's default `public` schema doesn't allow non-superusers to create
-- objects. The app's SP isn't a superuser, so without these GRANTs the app's
-- init_db() would fail (or, if you ran the SQL above, the SP would still be
-- unable to read/write the tables).
--
-- Replace <APP_SP_CLIENT_ID> with the value from
--   databricks apps get velocia-newop-sdc -o json | jq -r .service_principal_client_id
-- and uncomment the block.
-- ----------------------------------------------------------------------------

-- GRANT USAGE, CREATE  ON SCHEMA public                  TO "<APP_SP_CLIENT_ID>";
-- GRANT ALL            ON ALL TABLES    IN SCHEMA public TO "<APP_SP_CLIENT_ID>";
-- GRANT ALL            ON ALL SEQUENCES IN SCHEMA public TO "<APP_SP_CLIENT_ID>";
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public
--     GRANT ALL ON TABLES    TO "<APP_SP_CLIENT_ID>";
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public
--     GRANT ALL ON SEQUENCES TO "<APP_SP_CLIENT_ID>";


-- ----------------------------------------------------------------------------
-- 3. Seed data — 1 user, 5 studies, 5 access grants.
--
-- UUIDs are deterministic (uuid5 of "velocia-seed:<key>") so reruns are
-- idempotent and the seed resolves to the same primary keys regardless of
-- how often you run it. They match what scripts/seed_dev.py would produce.
-- ----------------------------------------------------------------------------

-- The user
INSERT INTO users (user_id, sso_subject, email, name)
VALUES (
    'f8c3bb43-2008-540c-b22f-7016cd9c9b8f',  -- uuid5 of <SEED_USER_EMAIL>
    '<SEED_USER_EMAIL>',
    '<SEED_USER_EMAIL>',
    '<SEED_USER_NAME>'
)
ON CONFLICT (sso_subject) DO UPDATE SET name = EXCLUDED.name;

-- 5 study documents
INSERT INTO study_documents (
    study_document_id, document_type, study_brief_title, study_acronym,
    study_id, study_status, last_modified_by, current_version
) VALUES
    ('d840fb18-a52b-5219-96a6-e9fcea9fb2f4', 'new_opportunity',
     'Tocavalumab in Moderate-to-Severe COPD with Frequent Exacerbations',
     'TOCA-COPD',     'D9999C00001', 'draft',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 1),
    ('655057b4-c267-596a-9b2d-4b59c45a3bde', 'new_opportunity',
     'Tezepelumab Adolescent Airway Remodeling Substudy',
     'TEZ-AAR',       'D9999C00002', 'draft',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 1),
    ('4bbfb00f-ccbc-5773-8900-240b81def500', 'new_opportunity',
     'Endometriosis Symptom Profiler — Real-World Evidence Cohort',
     'ENDO-PROFILE',  'D9999C00003', 'draft',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 1),
    ('0cac15b8-f03a-5d23-baa6-758bd63611ef', 'sdc',
     'Saxenda Cardiometabolic Phase IIb',
     'SAX-CARD-2B',   'D9999C00004', 'in_review',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 1),
    ('1baea00a-a2d8-5f28-90db-ebc66ff28d0e', 'sdc',
     'Imfinzi NSCLC Adjuvant Phase III',
     'IMF-ADJ-3',     'D9999C00005', 'approved',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 1)
ON CONFLICT (study_document_id) DO NOTHING;

-- 5 access grants (author on every doc)
INSERT INTO study_access_list (
    study_document_id, user_id, role, granted_by, is_active
) VALUES
    ('d840fb18-a52b-5219-96a6-e9fcea9fb2f4',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 'author',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', TRUE),
    ('655057b4-c267-596a-9b2d-4b59c45a3bde',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 'author',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', TRUE),
    ('4bbfb00f-ccbc-5773-8900-240b81def500',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 'author',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', TRUE),
    ('0cac15b8-f03a-5d23-baa6-758bd63611ef',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 'author',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', TRUE),
    ('1baea00a-a2d8-5f28-90db-ebc66ff28d0e',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', 'author',
     'f8c3bb43-2008-540c-b22f-7016cd9c9b8f', TRUE)
ON CONFLICT (study_document_id, user_id, role) DO NOTHING;


-- ----------------------------------------------------------------------------
-- 4. Sanity checks — should print 1 / 5 / 5
-- ----------------------------------------------------------------------------
SELECT 'users'             AS table_name, COUNT(*) AS rows FROM users
UNION ALL
SELECT 'study_documents'   , COUNT(*) FROM study_documents
UNION ALL
SELECT 'study_access_list' , COUNT(*) FROM study_access_list;
