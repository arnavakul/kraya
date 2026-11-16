-- ============================================================
-- PROCUREMENT REQUESTS
-- ============================================================

CREATE TABLE procurement_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL,

    requester_id UUID NOT NULL,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    category VARCHAR(100) NOT NULL,

    budget NUMERIC(19, 2),

    currency VARCHAR(3) NOT NULL DEFAULT 'INR',

    delivery_location VARCHAR(500) NOT NULL,

    required_by DATE,

    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- --------------------------------------------------------
    -- Foreign Keys
    -- --------------------------------------------------------

    CONSTRAINT fk_procurement_request_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id),

    CONSTRAINT fk_procurement_request_requester
        FOREIGN KEY (requester_id)
        REFERENCES users(id),

    -- --------------------------------------------------------
    -- Constraints
    -- --------------------------------------------------------

    CONSTRAINT chk_procurement_request_status
        CHECK (status IN (
            'DRAFT',
            'SUBMITTED',
            'VALIDATING',
            'SOURCING',
            'QUOTING',
            'EVALUATION',
            'NEGOTIATION',
            'APPROVAL',
            'PO_DRAFT',
            'COMPLETED',
            'REJECTED',
            'CANCELLED'
        )),

    CONSTRAINT chk_procurement_request_budget
        CHECK (budget IS NULL OR budget >= 0)
);


-- ============================================================
-- PROCUREMENT REQUEST INDEXES
-- ============================================================

CREATE INDEX idx_procurement_requests_organization_id
    ON procurement_requests(organization_id);

CREATE INDEX idx_procurement_requests_requester_id
    ON procurement_requests(requester_id);

CREATE INDEX idx_procurement_requests_status
    ON procurement_requests(status);

CREATE INDEX idx_procurement_requests_category
    ON procurement_requests(category);

CREATE INDEX idx_procurement_requests_required_by
    ON procurement_requests(required_by);


-- ============================================================
-- PROCUREMENT ITEMS
-- ============================================================

CREATE TABLE procurement_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    procurement_request_id UUID NOT NULL,

    description VARCHAR(500) NOT NULL,

    quantity NUMERIC(19, 3) NOT NULL,

    unit VARCHAR(50) NOT NULL,

    specifications TEXT,

    CONSTRAINT fk_procurement_item_request
        FOREIGN KEY (procurement_request_id)
        REFERENCES procurement_requests(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_procurement_item_quantity
        CHECK (quantity > 0)
);


-- ============================================================
-- PROCUREMENT ITEM INDEXES
-- ============================================================

CREATE INDEX idx_procurement_items_request_id
    ON procurement_items(procurement_request_id);