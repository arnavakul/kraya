
from langgraph.types import interrupt


def rfq_approval_node(state: dict) -> dict:
    rfq_drafts = state.get("rfq_drafts", [])

    if not rfq_drafts:
        return {
            "approval_status": "not_required",
            "workflow_status": "no_rfqs_to_approve"
        }

    # Pause execution and request human decisions.
    decisions = interrupt({
        "type": "rfq_approval_required",
        "message": "Review each RFQ and approve or reject it.",
        "rfq_drafts": [
            {
                "rfq_id": draft["rfq_id"],
                "supplier_name": draft["supplier"]["name"],
                "email_subject": draft["email_subject"],
                "email_body": draft["email_body"]
            }
            for draft in rfq_drafts
        ]
    })

    if not isinstance(decisions, dict):
        raise ValueError("Approval response must be a dictionary.")

    submitted_decisions = decisions.get("decisions")

    if not isinstance(submitted_decisions, list):
        raise ValueError("Approval decisions must be a list.")

    decision_map = {}

    for item in submitted_decisions:
        if not isinstance(item, dict):
            raise ValueError("Each decision must be a dictionary.")

        rfq_id = item.get("rfq_id")
        decision = item.get("decision")

        if decision not in ("approve", "reject"):
            raise ValueError(f"Invalid decision for RFQ {rfq_id}.")

        if rfq_id in decision_map:
            raise ValueError(f"Duplicate decision for RFQ {rfq_id}.")

        decision_map[rfq_id] = decision

    expected_ids = {draft["rfq_id"] for draft in rfq_drafts}

    if set(decision_map) != expected_ids:
        raise ValueError(
            "A decision must be submitted for every RFQ, "
            "with no unknown RFQ IDs."
        )

    updated_drafts = []
    approved_count = 0
    rejected_count = 0

    for draft in rfq_drafts:
        updated_draft = draft.copy()

        decision = decision_map[draft["rfq_id"]]

        if decision == "approve":
            updated_draft["status"] = "approved"
            approved_count += 1
        else:
            updated_draft["status"] = "rejected"
            rejected_count += 1

        updated_drafts.append(updated_draft)

    if approved_count == len(updated_drafts):
        workflow_status = "approved"
    elif rejected_count == len(updated_drafts):
        workflow_status = "rejected"
    else:
        workflow_status = "partially_approved"

    return {
        "rfq_drafts": updated_drafts,
        "approval_decisions": decisions,
        "approval_status": "completed",
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "workflow_status": workflow_status,
        "current_agent": "rfq_approval"
    }

