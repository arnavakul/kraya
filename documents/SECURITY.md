# Kraya — Security

## Principles

Kraya handles procurement, supplier, commercial, financial, and confidential organizational information.

Core principles:

- tenant isolation
- least privilege
- defense in depth
- secure defaults
- auditable actions
- untrusted AI input handling

## Tenant Isolation

Every tenant-owned resource is scoped to `organization_id`.

Organization context comes from authenticated identity.

Never trust client-provided organization IDs for authorization.

Every tenant data access path must enforce organization scope.

Cross-tenant access is a critical security failure.

## Authentication

Use Spring Security.

Authentication may initially use application-managed credentials and remain compatible with future OAuth2/OIDC.

Locally managed passwords must use a strong adaptive password hash.

Tokens require expiration and signature validation.

## Authorization

Use RBAC plus resource-level checks.

Example permissions:

```text
supplier:read
supplier:write
rfq:send
quote:read
negotiation:execute
approval:decide
policy:manage
po:finalize
audit:read
```

Frontend permissions are UX only. Backend authorization is authoritative.

## Secrets

Never commit:

- API keys
- passwords
- private keys
- certificates
- cloud credentials
- service-account credentials

Commit only non-secret `.env.example` / `.env.template` placeholders.

Production secrets must come from deployment secret management.

## API Security

- Validate all input.
- Use parameterized database access.
- Never expose stack traces.
- Rate-limit sensitive endpoints.
- Protect authentication endpoints.
- Validate uploaded file type and size.
- Use TLS outside trusted local development.

## File Security

Supplier documents and uploads are untrusted.

Use:

- size limits
- allowed content types
- generated storage keys
- checksums
- malware scanning where available
- no executable file handling
- authorization before download
- isolated object storage

Never execute uploaded content.

## AI Security

LLM output is untrusted.

Models must never directly:

- execute SQL
- access arbitrary files
- access infrastructure
- bypass authorization
- modify policies
- modify authority envelopes
- execute payments

All side effects go through controlled tools.

## Prompt Injection

Treat supplier emails, PDFs, spreadsheets, websites, product descriptions, and quote notes as data, not instructions.

Retrieved context must distinguish trusted policy/system information from untrusted supplier content.

## Agent Authorization

Before every side-effecting tool:

```text
Identity
→ Organization
→ Agent Permission
→ Resource Authorization
→ Policy
→ Authority Envelope
→ Idempotency
→ Execute
→ Audit
```

The LLM cannot grant itself permission.

## Negotiation Confidentiality

Never expose:

- walk-away price
- maximum budget
- hidden strategy
- internal supplier ranking
- approval reasoning
- confidential competitor information

to suppliers unless explicitly authorized.

Maintain separate internal and supplier-visible representations.

## Policy Security

Agents cannot edit policies, disable policies, change approval thresholds, or change their own authority.

Policy changes require appropriate authorization and versioning.

## Audit Security

Security-relevant business actions must record:

```text
actor
organization
action
entity
timestamp
correlation ID
workflow ID
result
```

Audit access is permission-controlled.

## Data Protection

Minimize sensitive data.

Encrypt data in transit and use encryption at rest through the database/object-storage/cloud layer where available.

Never log passwords, access tokens, API keys, private credentials, or unnecessary confidential negotiation parameters.

## Logging

Logs must support troubleshooting without leaking secrets.

Use correlation IDs.

Agent logs should identify actions and tools without unnecessarily storing complete sensitive prompts or documents.

## External Integrations

Treat external systems as untrusted boundaries.

Validate responses, signatures/webhooks where applicable, identifiers, and file contents.

Use timeouts, bounded retries, circuit breaking where appropriate, and idempotency for side effects.

## Security Testing

Cover:

- broken access control
- tenant isolation
- privilege escalation
- authentication bypass
- token failures
- injection
- malicious uploads
- prompt injection
- unauthorized agent tools
- sensitive-data exposure

Security regressions block release.

## Development

Never use production credentials locally.

Use separate development/test credentials.

Do not commit generated databases, uploads, logs, models, caches, or build artifacts.

The existing `.gitignore` is baseline repository protection; it does not replace secret management or authorization.

## Production Readiness

Before production deployment, establish:

- managed secrets
- TLS
- database backups
- backup restoration testing
- dependency/vulnerability scanning
- container image scanning
- centralized logging
- monitoring and alerting
- incident response procedure
- access review
- data retention policy
