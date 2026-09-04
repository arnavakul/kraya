CREATE TABLE users (
                       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                       organization_id UUID NOT NULL,

                       email VARCHAR(320) NOT NULL,

                       first_name VARCHAR(100) NOT NULL,

                       last_name VARCHAR(100) NOT NULL,

                       password_hash VARCHAR(255) NOT NULL,

                       role VARCHAR(30) NOT NULL,

                       status VARCHAR(20) NOT NULL,

                       created_at TIMESTAMP WITH TIME ZONE NOT NULL,

                       updated_at TIMESTAMP WITH TIME ZONE NOT NULL,

                       CONSTRAINT fk_users_organization
                           FOREIGN KEY (organization_id)
                               REFERENCES organizations(id),

                       CONSTRAINT uk_users_organization_email
                           UNIQUE (organization_id, email)
);