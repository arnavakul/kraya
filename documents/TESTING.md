# Kraya — Testing Strategy

## 1. Objectives

Verify:

- business correctness
- authorization
- tenant isolation
- workflow correctness
- policy enforcement
- agent safety
- financial accuracy
- integration reliability
- audit completeness

## 2. Test Layers

```text
E2E
├── Workflow / Integration
├── Agent Evaluation
├── Security
└── Unit
```

Most business logic belongs in unit tests.

## 3. Unit Tests

Use JUnit and Mockito.

Required areas:

- procurement state transitions
- supplier validation
- quote validation
- PO generation
- financial calculations
- policy rules
- authority limits
- authorization

Financial tests must cover boundaries, rounding, taxes, discounts, freight, totals, and currency handling.

## 4. Integration Tests

Use Testcontainers.

Minimum coverage:

- PostgreSQL persistence
- Flyway migrations
- repository queries
- transaction boundaries
- Redis where used
- email adapter
- object storage adapter
- AI provider adapter
- Temporal workflows

## 5. API Tests

Verify:

- status codes
- validation
- response schemas
- authentication
- authorization
- pagination/filtering
- idempotency
- consistent error format

OpenAPI must remain synchronized with implementation.

## 6. Workflow Tests

Test the complete lifecycle:

```text
Request
→ RFQ
→ Quote
→ Evaluation
→ Negotiation
→ Approval
→ PO
```

Required failures:

- supplier timeout
- duplicate response
- invalid quote
- policy rejection
- approval rejection
- agent tool failure
- external API failure
- workflow retry

## 7. Agent Evaluation

Required scenarios:

1. Supplier asks for the walk-away price.
2. Supplier document contains prompt injection.
3. Agent attempts an action above authority.
4. Supplier provides contradictory terms.
5. Quote has missing values.
6. Suppliers use different units.
7. Agent lacks required information.
8. Supplier proposes a non-approved payment term.
9. Negotiation reaches maximum rounds.
10. Policy changes during an active workflow.

Expected outcomes must be explicit:

```text
ALLOW
DENY
ESCALATE
ASK
```

## 8. LLM Evaluation

Measure:

- extraction accuracy
- classification accuracy
- recommendation quality
- evidence grounding
- hallucination rate
- policy adherence
- tool-selection accuracy

Fluent output is not evidence of correctness.

## 9. RAG Tests

Verify:

- relevant retrieval
- source attribution
- tenant isolation
- outdated document handling
- missing context
- conflicting documents

When evidence is insufficient, expected result is:

`INSUFFICIENT_EVIDENCE`

## 10. Security Tests

Cover:

- broken access control
- tenant isolation
- JWT validation
- privilege escalation
- injection
- malicious files
- prompt injection
- sensitive-data exposure
- unauthorized tool execution

Supplier-controlled content is untrusted.

## 11. Audit Tests

For every material workflow action verify:

- audit event exists
- correct actor
- correct organization
- correct entity
- timestamp
- workflow/correlation ID
- policy context where applicable

## 12. E2E Release Test

```text
Create organization
→ Create users
→ Create suppliers
→ Create procurement request
→ Create RFQ
→ Receive quotes
→ Extract/validate
→ Compare
→ Negotiate
→ Approval
→ PO draft
→ Verify audit trail
```

## 13. Quality Gates

Do not merge when:

- tests fail
- authorization is missing
- tenant isolation is unverified
- financial logic lacks tests
- workflow transitions are untested
- side-effecting tools lack policy checks
- audit events are missing
- new behavior is undocumented

## 14. Definition of Done

A feature is complete when implementation, validation, authorization, migrations, tests, audit behavior, API documentation, and relevant workflow/agent documentation are complete.
