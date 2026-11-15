
from agents.intake.agent import run_intake_agent

from agents.supplier_discovery.agent import (
    run_supplier_discovery_agent
)


def intake_node(state: dict) -> dict:

    result = run_intake_agent(
        user_input=state["user_input"],
        existing_requirement=state.get("requirement_draft")
    )

    return {
        "requirement_draft": result["requirement_draft"],
        "requirement": result["requirement"],
        "missing_fields": result["missing_fields"],
        "clarification_questions": result["clarification_questions"],
        "intake_errors": result["errors"],
        "intake_status": result["status"],
        "current_agent": "intake"
    }


def supplier_discovery_node(state: dict) -> dict:

    result = run_supplier_discovery_agent(
        requirement=state["requirement"]
    )

    result_data = result.model_dump(mode="json")

    return {
        "supplier_discovery_result": result_data,
        "supplier_candidates": result_data["suppliers"],
        "discovery_status": result_data["status"],
        "current_agent": "supplier_discovery"
    }
