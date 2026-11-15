
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
