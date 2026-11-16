"""Build a reply-scoped inbox context from an approved, dispatched RFQ."""

from typing import Any


def build_approved_rfq_inbox_context(
    procurement_state: dict[str, Any],
    rfq_id: str,
    dispatch_result: dict[str, Any],
) -> dict[str, Any]:
    """Return context only when the RFQ is approved and its dispatch succeeded.

    The dispatch provider message ID is the only existing identifier that can
    bind an inbound ``in_reply_to`` value to this RFQ. No IDs are generated.
    """
    contexts = procurement_state.get("approved_rfq_contexts", [])
    context = next(
        (item for item in contexts if str(item.get("rfq_id")) == str(rfq_id)),
        None,
    )
    if context is None:
        raise ValueError("No human-approved RFQ context matches this RFQ ID.")

    matching_draft = next(
        (
            item for item in procurement_state.get("rfq_drafts", [])
            if str(item.get("rfq_id")) == str(rfq_id)
        ),
        None,
    )
    if matching_draft is None or matching_draft.get("status") != "approved":
        raise ValueError("Only an approved RFQ can be handed to inbox triage.")

    if dispatch_result.get("status") != "sent":
        raise ValueError("Only a successfully dispatched RFQ can be handed off.")

    provider_message_id = dispatch_result.get("provider_message_id")
    if not isinstance(provider_message_id, str) or not provider_message_id.strip():
        raise ValueError("The successful dispatch has no provider message ID.")

    supplier = context.get("supplier") or {}
    if not context.get("organization_id"):
        raise ValueError("Approved RFQ context has no organization ID.")
    if not supplier.get("supplier_id"):
        raise ValueError("Approved RFQ context has no supplier ID.")
    if not supplier.get("contact_email"):
        raise ValueError("Approved RFQ context has no supplier contact email.")
    if not context.get("requirement"):
        raise ValueError("Approved RFQ context has no procurement requirement.")

    return {
        **context,
        "rfq_id": str(rfq_id),
        "supplier_id": str(supplier["supplier_id"]),
        "supplier_email": supplier["contact_email"].strip().lower(),
        "outbound_provider_message_id": provider_message_id,
    }


def build_inbox_triage_input(
    approved_rfq_context: dict[str, Any],
    **runtime_dependencies: Any,
) -> dict[str, Any]:
    """Prepare an inbox graph input while carrying actual policy identity.

    Runtime dependencies (connector, repositories and test doubles) are
    supplied by the caller. Negotiation policy is intentionally not inferred.
    """
    policy_request = approved_rfq_context.get("policy_evaluation_request")
    return {
        **runtime_dependencies,
        "approved_rfq_context": approved_rfq_context,
        **({"policy_evaluation_request": policy_request} if policy_request else {}),
    }

