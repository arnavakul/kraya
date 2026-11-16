
def route_after_intake(state: dict) -> str:

    if state.get("intake_status") == "validated":
        return "supplier_discovery"

    return "end"


def route_after_supplier_discovery(state: dict) -> str:

    if (
        state.get("discovery_status") == "completed"
        and state.get("supplier_candidates")
    ):
        return "rfq_drafting"

    return "end"

def route_after_rfq_drafting(state: dict) -> str:
    if (
        state.get("rfq_drafting_status") in ("completed", "partial")
        and state.get("rfq_drafts")
    ):
        return "approval"

    return "end"


def route_after_policy_guardrails(state: dict) -> str:
    if state.get("policy_decision") == "block":
        return "end"
    if state.get("policy_decision") in ("allow", "escalate"):
        return "approval_requests"
    return "end"


def route_after_approval_requests(state: dict) -> str:
    if (
        state.get("approval_request_status") == "pending"
        and state.get("approval_records")
    ):
        return "approval"
    return "end"
