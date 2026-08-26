# Kraya — API Specification

## Conventions

Base path:

```text
/api/v1
```

Use JSON for normal requests/responses and multipart/form-data for file uploads.

Use ISO-8601 timestamps and UUID resource identifiers.

## Authentication

```http
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

Protected endpoints require authenticated context.

Organization context is derived from authenticated identity.

## Response Format

Single resource:

```json
{ "data": {} }
```

Collection:

```json
{
  "data": [],
  "page": 0,
  "size": 20,
  "totalElements": 0
}
```

## Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request is invalid",
    "details": [],
    "correlationId": "uuid"
  }
}
```

Never expose stack traces or internal exception details.

## Suppliers

```http
GET    /api/v1/suppliers
POST   /api/v1/suppliers
GET    /api/v1/suppliers/{id}
PATCH  /api/v1/suppliers/{id}
DELETE /api/v1/suppliers/{id}
```

## Procurement Requests

```http
GET    /api/v1/procurement-requests
POST   /api/v1/procurement-requests
GET    /api/v1/procurement-requests/{id}
PATCH  /api/v1/procurement-requests/{id}
POST   /api/v1/procurement-requests/{id}/submit
POST   /api/v1/procurement-requests/{id}/cancel
```

Submission validates required fields and starts the configured workflow.

## Sourcing / RFQ

```http
POST /api/v1/sourcing-events
GET  /api/v1/sourcing-events/{id}

POST /api/v1/rfqs
GET  /api/v1/rfqs/{id}
POST /api/v1/rfqs/{id}/send
POST /api/v1/rfqs/{id}/close
```

Sending an RFQ requires an idempotency key.

## Quotes

```http
GET  /api/v1/rfqs/{rfqId}/quotes
GET  /api/v1/quotes/{id}
POST /api/v1/quotes
POST /api/v1/quotes/{id}/validate
```

Original quote documents remain immutable.

## Evaluation

```http
POST /api/v1/sourcing-events/{id}/evaluate
GET  /api/v1/sourcing-events/{id}/evaluation
```

Return deterministic commercial calculations plus AI recommendations/evidence where available.

## Negotiation

```http
POST /api/v1/negotiations
GET  /api/v1/negotiations/{id}
GET  /api/v1/negotiations/{id}/messages
POST /api/v1/negotiations/{id}/start
POST /api/v1/negotiations/{id}/message
POST /api/v1/negotiations/{id}/pause
POST /api/v1/negotiations/{id}/resume
POST /api/v1/negotiations/{id}/close
```

Every side-effecting operation requires authorization and policy validation.

## Approvals

```http
GET  /api/v1/approvals
GET  /api/v1/approvals/{id}
POST /api/v1/approvals/{id}/approve
POST /api/v1/approvals/{id}/reject
```

## Policies

```http
GET   /api/v1/policies
POST  /api/v1/policies
GET   /api/v1/policies/{id}
PATCH /api/v1/policies/{id}
POST  /api/v1/policies/{id}/activate
POST  /api/v1/policies/{id}/deactivate
```

Policy versions are preserved.

## Purchase Orders

```http
GET  /api/v1/purchase-orders
POST /api/v1/purchase-orders/drafts
GET  /api/v1/purchase-orders/{id}
POST /api/v1/purchase-orders/{id}/finalize
```

Finalization validates policy and approval requirements. MVP does not execute payment.

## Documents

```http
POST /api/v1/documents
GET  /api/v1/documents/{id}
GET  /api/v1/documents/{id}/download
```

Downloads verify organization access.

## Audit

```http
GET /api/v1/audit-events
GET /api/v1/audit-events/{id}
```

Audit data is read-only through the API.

## Real-Time Events

Use SSE for long-running workflow updates:

```http
GET /api/v1/workflows/{workflowId}/events
```

Possible events:

```text
WORKFLOW_STARTED
SUPPLIER_DISCOVERY_COMPLETED
RFQ_SENT
QUOTE_RECEIVED
QUOTE_ANALYZED
NEGOTIATION_STARTED
NEGOTIATION_UPDATED
APPROVAL_REQUIRED
APPROVAL_COMPLETED
PO_DRAFT_CREATED
WORKFLOW_COMPLETED
WORKFLOW_FAILED
```

## Pagination

Default:

```text
page=0
size=20
```

The backend must enforce a maximum page size.

## Idempotency

Required for side-effecting external operations.

```http
Idempotency-Key: <unique-key>
```

A repeated key for a completed operation returns the original result.

## Security Rules

- Authentication required for protected endpoints.
- Organization derived from authenticated context.
- Server-side authorization is mandatory.
- Resource tenant scope is checked.
- Sensitive fields are permission-controlled.
- Internal negotiation data is separate from supplier-visible data.
- Agent tools cannot bypass service authorization.

## Versioning

Breaking changes require a new API version.

Do not expose JPA entities directly as API contracts.
