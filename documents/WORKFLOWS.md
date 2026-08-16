# Kraya — Workflows

## 1. Procurement Lifecycle

```text
Requirement
→ Validation
→ Supplier Discovery
→ RFQ
→ Supplier Responses
→ Quote Normalization
→ Evaluation
→ Negotiation
→ Approval
→ PO Draft
→ Audit / Monitoring
```

Every transition has an explicit state and is auditable.

## 2. Procurement Request

States:

```text
DRAFT
SUBMITTED
VALIDATING
SOURCING
QUOTING
EVALUATION
NEGOTIATION
APPROVAL
PO_DRAFT
COMPLETED
REJECTED
CANCELLED
```

Invalid transitions are rejected.

## 3. Supplier Discovery

```text
Request
→ Extract requirements
→ Search approved sources
→ Rank candidates
→ Validate supplier information
→ Present candidates
```

Recommendations must expose evidence.

## 4. RFQ

```text
Create RFQ
→ Select suppliers
→ Validate eligibility
→ Generate RFQ
→ Required review
→ Send
→ Wait for responses
→ Close
```

Sending must be idempotent.

## 5. Quote

```text
Receive quote
→ Store original document
→ Extract fields
→ Validate extraction
→ Normalize
→ Persist
→ Compare
```

Original supplier documents remain immutable.

## 6. Evaluation

Deterministic calculation:

```text
line totals
+ freight
+ taxes
- discounts
= comparable commercial total
```

Then combine commercial comparison, supplier performance, risk, and requirement fit.

AI may explain results but cannot silently modify financial calculations.

## 7. Negotiation

```text
Select supplier
→ Create negotiation
→ Load authority envelope
→ Generate strategy
→ Prepare offer
→ Policy check
→ Send
→ Wait for response
→ Parse response
→ Evaluate
```

Outcomes:

- target achieved → approval/award
- continue → next round
- authority exceeded → approval
- deadline reached → close/escalate

Every supplier-facing message is attributable to a user or agent.

## 8. Approval

```text
Action requested
→ Policy evaluation
→ Approval required?
   ├─ No → continue
   └─ Yes → approval task → APPROVED / REJECTED
```

Rejected actions cannot continue automatically.

## 9. PO

```text
Award
→ Policy validation
→ Approval validation
→ Generate PO draft
→ Review
→ Finalize
```

MVP stops before payment execution.

## 10. Long-Running Workflows

Use Temporal for workflows that wait for supplier responses, approvals, negotiation responses, retries, or durable state over hours/days.

Short CRUD operations remain normal Spring service calls.

## 11. Exceptions

### Supplier timeout

Send configured reminder, record it, then close or escalate after deadline.

### Quote extraction failure

Preserve source document, mark extraction failure, and request review.

### Policy block

Stop, create approval/escalation if applicable, and audit.

### External service failure

Retry with bounded backoff and idempotency; escalate after the retry limit.

### Agent uncertainty

Do not fabricate; request clarification or human review.

## 12. Audit

Every business-state-changing workflow action records:

```text
workflow_id
correlation_id
actor
action
entity
previous_state
new_state
timestamp
result
policy_context
```
