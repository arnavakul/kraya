# Kraya — Architecture

## Architecture Style

Kraya starts as a **modular monolith**. Do not split the MVP into microservices.

```text
React
  ↓
REST / SSE
  ↓
Spring Boot
  ├── Auth / Organization / User
  ├── Supplier
  ├── Procurement
  ├── Sourcing / RFQ
  ├── Quote / Evaluation
  ├── Negotiation
  ├── Approval / Policy
  ├── Purchase Order
  ├── Document
  ├── Agent
  ├── Audit
  └── Integration
       ├── Email
       ├── LLM
       ├── Object Storage
       └── Supplier Sources
  ↓
PostgreSQL + pgvector
Redis / Temporal where required
```

## Backend Structure

```text
com.kraya
├── auth
├── organization
├── user
├── supplier
├── procurement
├── sourcing
├── quote
├── evaluation
├── negotiation
├── approval
├── policy
├── purchaseorder
├── document
├── agent
├── audit
├── integration
└── common
```

Controllers stay thin. Business rules belong in application/domain services.

## Request Flow

```text
Controller
  ↓
Application Service
  ↓
Domain Logic
  ↓
Repository / Integration
  ↓
Database / External System
```

Cross-cutting concerns: security, validation, transactions, audit, and observability.

## AI Architecture

LLMs are accessed through an AI abstraction layer.

```text
Agent
  ↓
Agent Runtime
  ↓
AI Gateway
  ├── Model Provider
  ├── Prompt Registry
  ├── Structured Output
  ├── Embeddings
  └── Retrieval
```

Agents never access repositories directly. They use registered tools.

```text
Agent
  ↓
Tool
  ↓
Authorization
  ↓
Policy Engine
  ↓
Domain Service
  ↓
Database / External System
```

## RAG

Initial vector storage uses PostgreSQL + pgvector.

```text
Document → Extraction → Chunking → Embedding → pgvector
```

Retrieval is always scoped to the current organization and returns source-aware context.

## Workflow Architecture

Use normal Spring services for short operations.

Use Temporal for durable workflows involving supplier responses, approvals, negotiations, retries, or long-running procurement state.

```text
Temporal Workflow
  ↓
Activities
  ↓
Spring Domain Services
```

Temporal orchestrates; business rules remain in application/domain services.

## Audit and Correlation

Material state changes create audit records.

Use correlation IDs across:

`HTTP Request → Workflow → Agent Run → Tool Call → External Request`

## Data and Transactions

PostgreSQL is the procurement system of record.

Use transactions for atomic business changes.

External side effects are not assumed to be transactional with PostgreSQL. Use idempotency and durable workflow state.

## Integrations

External providers are isolated behind interfaces/adapters:

```text
EmailProvider
LLMProvider
ObjectStorageProvider
SupplierSourceProvider
```

Domain modules must not depend directly on provider SDKs.

## API

Public APIs use `/api/v1/...`.

REST is the default. Use SSE/WebSocket only for genuine real-time workflow or agent updates.

## Documents

Binary documents live in object storage; PostgreSQL stores metadata.

```text
Document
 ├── metadata → PostgreSQL
 └── content  → Object Storage
```

## Redis

Redis is optional infrastructure, never the source of truth.

Use it for short-lived caching, rate limiting, or required distributed coordination.

## Frontend

React consumes the versioned API.

Use TanStack Query for server state. Frontend permissions are UX only; backend authorization is authoritative.

## Deployment Evolution

Development uses Spring Boot, PostgreSQL, Redis, Temporal, and React.

Production infrastructure is added later:

```text
Load Balancer
  ↓
Application
  ↓
Managed PostgreSQL
  ↓
Redis
  ↓
Temporal
  ↓
Object Storage
```

Docker, cloud, Kubernetes, CI/CD, observability, and autoscaling are deployment concerns and should be introduced after the MVP is stable.
