CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    procurement_request_id UUID NOT NULL REFERENCES procurement_requests(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL,
    result JSONB,
    error_message VARCHAR(1000),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_runs_request ON agent_runs(organization_id, procurement_request_id, started_at DESC);
