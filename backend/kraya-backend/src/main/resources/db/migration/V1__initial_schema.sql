CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- ORGANIZATIONS
-- ============================================================

CREATE TABLE organizations (
                               id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                               legal_name VARCHAR(255) NOT NULL,

                               trade_name VARCHAR(255),

                               organization_type VARCHAR(30) NOT NULL,

                               status VARCHAR(30) NOT NULL DEFAULT 'PENDING_VERIFICATION',

                               country_code VARCHAR(2) NOT NULL,

                               primary_email VARCHAR(320) NOT NULL,

                               primary_phone VARCHAR(30),

                               website_url VARCHAR(500),

                               preferred_language VARCHAR(10) NOT NULL DEFAULT 'en-IN',

                               currency_code VARCHAR(3) NOT NULL DEFAULT 'INR',

                               timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',

                               is_verified BOOLEAN NOT NULL DEFAULT FALSE,

                               parent_organization_id UUID,

                               created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                               updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,


    -- --------------------------------------------------------
    -- Constraints
    -- --------------------------------------------------------

                               CONSTRAINT chk_organization_type
                                   CHECK (organization_type IN (
                                                                'BUYER',
                                                                'SUPPLIER',
                                                                'BOTH'
                                       )),

                               CONSTRAINT chk_organization_status
                                   CHECK (status IN (
                                                     'PENDING_VERIFICATION',
                                                     'ACTIVE',
                                                     'SUSPENDED',
                                                     'DEACTIVATED'
                                       )),

                               CONSTRAINT fk_organization_parent
                                   FOREIGN KEY (parent_organization_id)
                                       REFERENCES organizations(id)
                                       ON DELETE SET NULL
);


-- ============================================================
-- ORGANIZATION INDEXES
-- ============================================================

CREATE INDEX idx_organizations_status
    ON organizations(status);

CREATE INDEX idx_organizations_type
    ON organizations(organization_type);

CREATE INDEX idx_organizations_country
    ON organizations(country_code);

CREATE INDEX idx_organizations_parent
    ON organizations(parent_organization_id);


-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
                       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                       organization_id UUID NOT NULL,

                       email VARCHAR(320) NOT NULL,

                       name VARCHAR(255) NOT NULL,

                       password_hash VARCHAR(255),

                       status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

                       created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

                       updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,


    -- --------------------------------------------------------
    -- Constraints
    -- --------------------------------------------------------

                       CONSTRAINT fk_user_organization
                           FOREIGN KEY (organization_id)
                               REFERENCES organizations(id)
                               ON DELETE CASCADE,

                       CONSTRAINT uq_user_organization_email
                           UNIQUE (organization_id, email),

                       CONSTRAINT chk_user_status
                           CHECK (status IN (
                                             'ACTIVE',
                                             'SUSPENDED',
                                             'DEACTIVATED'
                               ))
);


-- ============================================================
-- USER INDEXES
-- ============================================================

CREATE INDEX idx_users_organization_id
    ON users(organization_id);

CREATE INDEX idx_users_email
    ON users(email);

CREATE INDEX idx_users_status
    ON users(status);