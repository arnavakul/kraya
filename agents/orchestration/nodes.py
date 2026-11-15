
from agents.intake.agent import run_intake_agent

from agents.supplier_discovery.agent import (
    run_supplier_discovery_agent
)

from agents.rfq_drafting.agent import (
    run_rfq_drafting_agent
)

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate


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



def rfq_drafting_node(state: dict) -> dict:

    requirement = Requirement.model_validate(
        state["requirement"]
    )

    # Extract supplier objects from discovery assessments
    suppliers = [
        SupplierCandidate.model_validate(
            assessment["supplier"]
        )
        for assessment in state.get("supplier_candidates", [])
    ]

    result = run_rfq_drafting_agent(
        requirement=requirement,
        suppliers=suppliers
    )

    result_data = result.model_dump(mode="json")

    return {
        "rfq_drafting_result": result_data,
        "rfq_drafts": result_data["rfq_drafts"],
        "rfq_drafting_status": result_data["status"],
        "current_agent": "rfq_drafting",
        "workflow_status": (
            "pending_approval"
            if result_data["successful_drafts"] > 0
            else "rfq_drafting_failed"
        )
    }
