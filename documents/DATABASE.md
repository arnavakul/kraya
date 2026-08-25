# Kraya — Database Design

## Database

- PostgreSQL
- Flyway for migrations
- pgvector for initial RAG retrieval

PostgreSQL is the source of truth for procurement state.

## General Rules

Tenant-owned business tables contain `organization_id`.

Use UUID primary keys and UTC timestamps.

Use `created_at` and `updated_at` where applicable.

Never store plaintext passwords or secrets.

## Identity

### organizations

```text
id
name
status
created_at
updated_at
```

### users

```text
id
organization_id
email
password_hash / identity_reference
name
status
created_at
updated_at
```

### roles

```text
id
organization_id
name
```

### user_roles

```text
user_id
role_id
```

## Suppliers

### suppliers

```text
id
organization_id
legal_name
display_name
tax_identifier
website
status
risk_level
rating
created_at
updated_at
```

### supplier_contacts

```text
id
supplier_id
name
email
phone
designation
```

### supplier_addresses

```text
id
supplier_id
address_type
address_line
city
state
postal_code
country
```

## Procurement

### procurement_requests

```text
id
organization_id
requester_id
title
description
category
budget
currency
delivery_location
required_by
status
created_at
updated_at
```

### procurement_items

```text
id
procurement_request_id
description
quantity
unit
specifications
```

## Sourcing

### sourcing_events

```text
id
organization_id
procurement_request_id
status
opens_at
closes_at
```

### rfqs

```text
id
sourcing_event_id
reference_number
status
sent_at
deadline
```

### rfq_suppliers

```text
id
rfq_id
supplier_id
status
invited_at
responded_at
```

## Quotes

### quotes

```text
id
rfq_supplier_id
source_document_id
currency
subtotal
tax_total
discount_total
freight_total
grand_total
validity_until
status
extraction_status
```

### quote_lines

```text
id
quote_id
procurement_item_id
description
quantity
unit
unit_price
tax
discount
line_total
```

Financial totals are calculated and validated by application code.

## Negotiation

### negotiations

```text
id
organization_id
supplier_id
sourcing_event_id
status
target_amount
maximum_authorized_amount
deadline
maximum_rounds
```

### negotiation_rounds

```text
id
negotiation_id
round_number
actor_type
status
created_at
```

### negotiation_messages

```text
id
negotiation_round_id
sender_type
message
external_message_id
sent_at
```

Internal strategy and confidential authority data must not be stored in supplier-visible message fields.

## Policies and Approvals

### policies

```text
id
organization_id
name
version
status
definition
effective_from
created_at
```

### approvals

```text
id
organization_id
entity_type
entity_id
status
requested_by
decided_by
decision
comment
created_at
decided_at
```

## Purchase Orders

### purchase_orders

```text
id
organization_id
supplier_id
procurement_request_id
reference_number
status
subtotal
tax_total
grand_total
currency
delivery_terms
payment_terms
created_at
updated_at
```

### purchase_order_lines

```text
id
purchase_order_id
procurement_item_id
description
quantity
unit
unit_price
tax
line_total
```

## Documents

### documents

```text
id
organization_id
owner_type
owner_id
filename
content_type
storage_key
size_bytes
checksum
extraction_status
created_at
```

### document_chunks

```text
id
document_id
chunk_index
content
embedding
metadata
```

Embeddings inherit tenant scope through the owning document.

## Agent Records

### agent_runs

```text
id
organization_id
workflow_id
agent_type
model_provider
model_name
status
started_at
completed_at
error_code
```

### agent_tool_calls

```text
id
agent_run_id
tool_name
input_reference
output_reference
status
created_at
```

Avoid storing sensitive payloads unnecessarily.

## Audit

### audit_events

```text
id
organization_id
actor_type
actor_id
action
entity_type
entity_id
previous_state
new_state
workflow_id
correlation_id
metadata
created_at
```

Audit records are append-only from normal application behavior.

## Relationship Model

```text
Organization
 ├── Users
 ├── Suppliers
 ├── Policies
 ├── Procurement Requests
 │     └── Items
 ├── Sourcing Events
 │     └── RFQs
 │           └── Suppliers
 │                 └── Quotes
 │                       └── Quote Lines
 ├── Negotiations
 │     └── Rounds
 │           └── Messages
 ├── Approvals
 ├── Purchase Orders
 ├── Documents
 ├── Agent Runs
 └── Audit Events
```

## Constraints

- Foreign keys enforce valid relationships.
- Monetary values cannot be negative unless explicitly required by a domain rule.
- Quantities must be positive.
- Tenant scope is mandatory.
- Workflow transitions are validated in application code.
- Unique business references have database constraints.

## Migrations

Every schema change requires a new Flyway migration.

Never modify an applied migration.

```text
V1__initial_schema.sql
V2__add_supplier_risk.sql
V3__add_negotiation_tables.sql
```
