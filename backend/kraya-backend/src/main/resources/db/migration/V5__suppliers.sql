-- V5: supplier directory. Each buyer organization keeps its own list of suppliers.
-- Suppliers are plain records here (not platform users); they become RFQ recipients in the next phase.

CREATE TABLE suppliers (
                           id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
                           organization_id UUID          NOT NULL,
                           name            VARCHAR(255)  NOT NULL,
                           contact_name    VARCHAR(255),
                           contact_email   VARCHAR(320)  NOT NULL,
                           contact_phone   VARCHAR(30),
                           country_code    VARCHAR(2)    NOT NULL,
                           website_url     VARCHAR(500),
                           tax_id          VARCHAR(50),
                           payment_terms   VARCHAR(255),
                           notes           VARCHAR(2000),
                           status          VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',
                           status_reason   VARCHAR(500),
                           created_by      UUID          NOT NULL,
                           version         BIGINT        NOT NULL DEFAULT 0,
                           created_at      TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           updated_at      TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,

                           CONSTRAINT fk_suppliers_organization
                               FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE RESTRICT,

                           CONSTRAINT fk_suppliers_created_by
                               FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,

                           CONSTRAINT chk_suppliers_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'BLOCKED')),
                           CONSTRAINT chk_suppliers_country_upper CHECK (country_code = upper(country_code)),
                           CONSTRAINT chk_suppliers_email_lower CHECK (contact_email = lower(contact_email))
);

-- One supplier per email within an organization.
CREATE UNIQUE INDEX uq_suppliers_org_email ON suppliers (organization_id, contact_email);
CREATE INDEX idx_suppliers_org_status ON suppliers (organization_id, status);


CREATE TABLE supplier_categories (
                                     supplier_id UUID         NOT NULL,
                                     category    VARCHAR(100) NOT NULL,

                                     PRIMARY KEY (supplier_id, category),

                                     CONSTRAINT fk_supplier_categories_supplier
                                         FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE CASCADE
);

CREATE INDEX idx_supplier_categories_category ON supplier_categories (lower(category));
