# Kraya — Agent Specification

## 1. Principles

Kraya agents are controlled software components. Every agent operates within:

- defined goal
- explicit tools
- organization context
- policy constraints
- authority limits
- available evidence
- auditable workflow

LLMs never receive direct database or infrastructure access.

## 2. Runtime

```text
Workflow
  ↓
Agent
  ↓
Context + RAG
  ↓
LLM
  ↓
Structured decision
  ↓
Tool selection
  ↓
Authorization + Policy
  ↓
Tool execution
  ↓
Audit
```

Side-effecting tools must be authorized immediately before execution.

## 3. MVP Agents

### Intake Agent

Converts unstructured requirements into structured requirements.

May output category, items, quantities, specifications, delivery requirements, budget, and missing information.

Cannot approve, communicate with suppliers, or create a PO.

### Supplier Discovery Agent

Identifies candidate suppliers from approved sources and provides evidence, relevance, and risks.

Cannot approve suppliers or commit spend.

### Quote Analysis Agent

Extracts and explains quote data from documents and identifies discrepancies or missing fields.

Extracted values require validation before becoming authoritative.

### Evaluation Agent

Ranks suppliers using normalized quotes, deterministic comparisons, supplier performance, risk, and requirement fit.

Cannot override policy or approve its own recommendation.

### Negotiation Agent

Negotiates with suppliers within an explicit authority envelope.

May send counteroffers, request clarification, and request revised quotes when permitted.

Cannot reveal confidential targets, exceed authority, bypass approvals, execute payment, or finalize an unauthorized PO.

## 4. Authority Envelope

A negotiation-capable agent receives:

```text
maximum_spend
target_price
walkaway_price
allowed_concessions
allowed_terms
maximum_rounds
deadline
approval_conditions
```

Application code enforces these values. The LLM cannot modify them.

## 5. Tool Access

Agents use registered tools such as:

```text
searchSuppliers
getSupplier
createRFQ
sendRFQ
getQuotes
compareQuotes
getPolicy
requestApproval
sendSupplierMessage
createPODraft
```

Each tool verifies organization scope, agent permission, policy, authority, and idempotency where applicable.

## 6. Human-in-the-Loop

Approval is required when configured by policy, including high spend, new/unapproved suppliers, legal/contract changes, authority breaches, unusual payment terms, or compliance exceptions.

The agent stops and creates an approval task.

## 7. Failure Rules

| Condition             | Agent behavior                |
| --------------------- | ----------------------------- |
| Missing information   | Ask / escalate                |
| Conflicting evidence  | Flag / escalate               |
| Policy block          | Stop                          |
| Tool failure          | Retry through workflow policy |
| Repeated failure      | Escalate                      |
| Insufficient evidence | Do not fabricate              |

## 8. Prompt Injection

Supplier emails, documents, websites, and quotations are untrusted content. Instructions contained in supplier-controlled content are never treated as Kraya system instructions.

## 9. Observability

Record agent type, workflow ID, organization ID, context references, model/provider, tool calls, policy decisions, final action, escalation, latency, and cost metadata where available.

## 10. Deterministic vs AI Responsibilities

Use application code for:

- calculations
- permissions
- policy enforcement
- state transitions
- financial totals
- approval decisions

Use LLMs for:

- interpretation
- extraction
- summarization
- classification
- recommendation
- natural-language negotiation
