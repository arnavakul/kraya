-- V2: users. Login is by email alone, so email is globally unique and stored lowercase.

CREATE TABLE users (
                       id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
                       organization_id UUID         NOT NULL,
                       email           VARCHAR(320) NOT NULL,
                       first_name      VARCHAR(100) NOT NULL,
                       last_name       VARCHAR(100) NOT NULL,
                       password_hash   VARCHAR(255) NOT NULL,
                       role            VARCHAR(30)  NOT NULL,
                       status          VARCHAR(30)  NOT NULL DEFAULT 'ACTIVE',
                       created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       updated_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- RESTRICT: deleting an organization must not silently delete its users.
                       CONSTRAINT fk_users_organization
                           FOREIGN KEY (organization_id)
                               REFERENCES organizations (id)
                               ON DELETE RESTRICT,

                       CONSTRAINT uq_users_email UNIQUE (email),

    -- The app normalizes emails to lowercase; the database enforces it.
                       CONSTRAINT chk_users_email_lowercase CHECK (email = lower(email)),

                       CONSTRAINT chk_users_status
                           CHECK (status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED'))

    -- Add a CHECK on role once the UserRole enum is final.
);

CREATE INDEX idx_users_organization_id ON users (organization_id);