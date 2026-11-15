
def route_after_intake(state: dict) -> str:

    if state.get("intake_status") == "validated":
        return "supplier_discovery"

    return "end"
