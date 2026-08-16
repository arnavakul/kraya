# Kraya — Requirements

## 1. Scope

Kraya is an AI-native procurement platform covering procurement requests, supplier discovery, RFQs, quote evaluation, controlled negotiation, approvals, purchase-order drafts, documents, and audit history.

### MVP

- Organization and user management
- RBAC
- Supplier management
- Procurement requests
- Supplier discovery
- RFQ creation/distribution
- Supplier responses and quote capture
- Quote comparison
- Policy and approval rules
- AI-assisted supplier/quote analysis
- Controlled AI negotiation
- PO drafts
- Audit trail
- Document storage and retrieval
- RAG over approved organizational and supplier data

### Out of scope

- Autonomous payment execution
- Full ERP replacement
- Inventory management
- Supplier marketplace
- Native mobile application
- Kubernetes production deployment

## 2. Roles

| Role                | Responsibility                       |
| ------------------- | ------------------------------------ |
| ADMIN               | Organization, users, roles, policies |
| PROCUREMENT_MANAGER | Sourcing and procurement             |
| PROCUREMENT_ANALYST | Requests, RFQs, evaluations          |
| REQUESTER           | Creates and tracks requests          |
| APPROVER            | Reviews approval tasks               |
| FINANCE             | Budget and commercial review         |

## 3. Functional Requirements

### FR-01 Authentication and Authorization

The system shall enforce authenticated access, organization isolation, RBAC, and permission checks for every protected operation.

### FR-02 Supplier Management

Users shall be able to create, view, update, deactivate, categorize, and maintain contacts, documents, commercial information, performance, and risk data for suppliers.

### FR-03 Procurement Requests

A request shall support title, description, category, items, quantities, delivery date, delivery location, budget, and attachments.

### FR-04 Supplier Discovery

Kraya shall identify candidate suppliers using approved supplier data, product/category information, historical data, and approved external sources where integrated. AI recommendations shall include evidence.

### FR-05 RFQ

Users shall create RFQs, select suppliers, set deadlines, send RFQs, track responses, and close RFQs.

### FR-06 Quote Processing

Kraya shall capture supplier, item, quantity, unit price, taxes, discounts, freight, delivery terms, payment terms, warranty, validity, and source document.

AI extraction shall be treated as untrusted until validated.

### FR-07 Quote Evaluation

The application shall deterministically calculate price, taxes, discounts, freight, delivery, payment terms, warranty, and applicable total cost of ownership. AI may explain or recommend but shall not replace financial calculations.

### FR-08 Policy Engine

Policies shall define spending limits, approval requirements, supplier restrictions, negotiation authority, documentation requirements, and compliance conditions. Policies shall be versioned and auditable.

### FR-09 Approval

Approval records shall include approver, decision, timestamp, reason/comment, and triggering policy/rule.

### FR-10 AI Agents

Agents may interpret requirements, identify suppliers, analyze quotes, recommend strategies, communicate within authority, request approval, and prepare PO drafts.

Agents shall never bypass policy, authorization, approval, or audit controls.

### FR-11 Negotiation

A negotiation shall define target price, maximum authorized price, concessions, allowed terms, maximum rounds, deadline, and approval conditions. The agent shall operate only within this authority envelope.

### FR-12 Purchase Orders

Kraya shall generate PO drafts containing buyer, supplier, items, quantities, prices, taxes, delivery terms, payment terms, references, and approval status. MVP does not execute payment.

### FR-13 Audit

Material actions shall create audit events identifying actor, action, entity, timestamp, result, policy/approval context, and workflow/correlation ID.

### FR-14 Documents and RAG

Documents shall be stored with metadata. Approved documents may be indexed for retrieval. RAG responses shall retain source references.

## 4. Non-Functional Requirements

### Security

- TLS for external communication
- No plaintext passwords
- Secrets outside source control
- Least-privilege authorization
- Tenant isolation
- Auditable privileged operations

### Reliability

- Transactional state changes
- Idempotency for retryable external operations
- Explicit workflow states
- Bounded retries
- No duplicate supplier messages or PO creation caused by retries

### AI Safety

- Structured model outputs
- Tool-level authorization
- Policy validation before side effects
- Human approval for configured high-risk actions
- Prompt-injection resistance for supplier content
- LLM output treated as untrusted input

### Performance

Normal CRUD operations shall not require unnecessary LLM calls. Long-running AI/procurement workflows shall execute asynchronously.

### Observability

Traceable correlation:

`user → API → workflow → agent → tool → external system`

### Maintainability

- Modular Spring Boot architecture
- Clear domain boundaries
- Flyway migrations
- API documentation
- Automated tests
- No business logic in controllers

## 5. Technology Constraints

- Java + Spring Boot
- Spring Security
- Spring Data JPA
- PostgreSQL
- Flyway
- Redis where required
- pgvector initially
- Temporal for durable long-running workflows
- REST
- SSE/WebSocket where real-time updates are required
