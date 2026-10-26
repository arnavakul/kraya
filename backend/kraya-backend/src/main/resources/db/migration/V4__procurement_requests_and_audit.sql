-- V4: procurement requests (+ line items) and the audit trail.

CREATE SEQUENCE procurement_request_seq START 1;

CREATE TABLE procurement_requests (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID          NOT NULL,
    reference         VARCHAR(30)   NOT NULL,
    title             VARCHAR(255)  NOT NULL,
    description       VARCHAR(4000),
    category          VARCHAR(100),
    budget_amount     NUMERIC(15,2),
    currency_code     VARCHAR(3)    NOT NULL DEFAULT 'INR',
    needed_by         DATE,
    delivery_location VARCHAR(255),
    status            VARCHAR(30)   NOT NULL DEFAULT 'DRAFT',
    status_reason     VARCHAR(500),
    created_by        UUID          NOT NULL,
    version           BIGINT        NOT NULL DEFAULT 0,   -- optimistic locking
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_procurement_requests_reference UNIQUE (reference),

    CONSTRAINT fk_procurement_requests_organization
        FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE RESTRICT,

    CONSTRAINT fk_procurement_requests_created_by
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,

    CONSTRAINT chk_procurement_requests_status CHECK (status IN (
        'DRAFT', 'SUBMITTED', 'VALIDATING', 'SOURCING', 'QUOTING', 'EVALUATION',
        'NEGOTIATION', 'APPROVAL', 'PO_DRAFT', 'COMPLETED', 'REJECTED', 'CANCELLED'
    )),

    CONSTRAINT chk_procurement_requests_budget
        CHECK (budget_amount IS NULL OR budget_amount >= 0),

    CONSTRAINT chk_procurement_requests_currency_upper
        CHECK (currency_code = upper(currency_code))
);

CREATE INDEX idx_procurement_requests_org_status
    ON procurement_requests (organization_id, status);

CREATE INDEX idx_procurement_requests_org_created
    ON procurement_requests (organization_id, created_at DESC);


CREATE TABLE procurement_request_items (
    id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id  UUID          NOT NULL,
    line_no     INTEGER       NOT NULL,
    name        VARCHAR(255)  NOT NULL,
    description VARCHAR(2000),
    quantity    NUMERIC(14,3) NOT NULL,
    unit        VARCHAR(30)   NOT NULL,

    CONSTRAINT fk_request_items_request
        FOREIGN KEY (request_id) REFERENCES procurement_requests (id) ON DELETE CASCADE,

    CONSTRAINT chk_request_items_quantity CHECK (quantity > 0)
);

CREATE INDEX idx_request_items_request ON procurement_request_items (request_id);


-- Append-only: rows are inserted, never updated or deleted by the application.
CREATE TABLE audit_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID         NOT NULL,
    correlation_id  VARCHAR(64),
    actor_user_id   UUID,
    action          VARCHAR(60)  NOT NULL,
    entity_type     VARCHAR(60)  NOT NULL,
    entity_id       UUID         NOT NULL,
    previous_state  VARCHAR(30),
    new_state       VARCHAR(30),
    result          VARCHAR(20)  NOT NULL DEFAULT 'SUCCESS',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_events_organization
        FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE RESTRICT,

    CONSTRAINT fk_audit_events_actor
        FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_events_entity
    ON audit_events (organization_id, entity_type, entity_id, created_at);