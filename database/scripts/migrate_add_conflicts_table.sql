-- Decision Conflict Detection Table
-- Run once against the live DB:
--   psql $DATABASE_URL -f scripts/migrate_add_conflicts_table.sql

CREATE TABLE IF NOT EXISTS decision_conflicts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_a_id   UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    decision_b_id   UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    conflict_type   VARCHAR(50) NOT NULL,   -- 'direct', 'indirect', 'potential'
    explanation     TEXT,
    severity        VARCHAR(10) NOT NULL,   -- 'low', 'medium', 'high'
    detected_at     TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_conflict_pair UNIQUE (decision_a_id, decision_b_id),
    CONSTRAINT no_self_conflict CHECK (decision_a_id <> decision_b_id)
);

CREATE INDEX IF NOT EXISTS idx_conflicts_a  ON decision_conflicts (decision_a_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_b  ON decision_conflicts (decision_b_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_severity ON decision_conflicts (severity);
