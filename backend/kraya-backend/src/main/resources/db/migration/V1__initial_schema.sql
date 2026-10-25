-- V1: organizations (tenant root).
-- Users live in V2, refresh tokens in V3.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE organizations (
                               id                     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
                               legal_name             VARCHAR(255) NOT NULL,
                               trade_name             VARCHAR(255),
                               organization_type      VARCHAR(30)  NOT NULL,
                               status                 VARCHAR(30)  NOT NULL DEFAULT 'PENDING_VERIFICATION',
                               country_code           VARCHAR(2)   NOT NULL,
                               primary_email          VARCHAR(320) NOT NULL,
                               primary_phone          VARCHAR(30),
                               website_url            VARCHAR(500),
                               preferred_language     VARCHAR(10)  NOT NULL DEFAULT 'en-IN',
                               currency_code          VARCHAR(3)   NOT NULL DEFAULT 'INR',
                               timezone               VARCHAR(50)  NOT NULL DEFAULT 'Asia/Kolkata',
                               is_verified            BOOLEAN      NOT NULL DEFAULT FALSE,
                               parent_organization_id UUID,
                               created_at             TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               updated_at             TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

                               CONSTRAINT chk_organizations_type
                                   CHECK (organization_type IN ('BUYER', 'SUPPLIER', 'BOTH')),

                               CONSTRAINT chk_organizations_status
                                   CHECK (status IN ('PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED')),

                               CONSTRAINT chk_organizations_country_upper
                                   CHECK (country_code = upper(country_code)),

                               CONSTRAINT chk_organizations_currency_upper
                                   CHECK (currency_code = upper(currency_code)),

                               CONSTRAINT chk_organizations_not_own_parent
                                   CHECK (parent_organization_id IS NULL OR parent_organization_id <> id),

                               CONSTRAINT fk_organizations_parent
                                   FOREIGN KEY (parent_organization_id)
                                       REFERENCES organizations (id)
                                       ON DELETE SET NULL
);

-- OrganizationService.existsByPrimaryEmailIgnoreCase(...) is backed by this index.
CREATE UNIQUE INDEX uq_organizations_primary_email
    ON organizations (lower(primary_email));

CREATE INDEX idx_organizations_status  ON organizations (status);
CREATE INDEX idx_organizations_type    ON organizations (organization_type);
CREATE INDEX idx_organizations_country ON organizations (country_code);
CREATE INDEX idx_organizations_parent  ON organizations (parent_organization_id)
    WHERE parent_organization_id IS NOT NULL;