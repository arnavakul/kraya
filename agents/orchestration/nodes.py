
from agents.intake.agent import run_intake_agent

from agents.supplier_discovery.agent import (
    run_supplier_discovery_agent
)

from agents.rfq_drafting.agent import (
    run_rfq_drafting_agent
)

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate
from tools.rfq.supplier_eligibility import evaluate_supplier_eligibility
from schemas.policy import (
    CheckStatus,
    PolicyCheckResult,
    PolicyDecision,
    PolicyEvaluationResult,
    RiskLevel,
)
from pydantic import ValidationError
from schemas.policy import PolicyEvaluationRequest


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

    candidate_assessments = state.get("supplier_candidates", [])
    eligibility_results = []
    eligible_suppliers = []
    suppliers_requiring_review = []

    for assessment in candidate_assessments:
        eligibility = evaluate_supplier_eligibility(assessment)
        eligibility_results.append(eligibility)

        if eligibility.get("eligible"):
            eligible_suppliers.append(
                SupplierCandidate.model_validate(assessment["supplier"])
            )
        elif eligibility.get("decision") == "manual_review":
            suppliers_requiring_review.append(assessment["supplier"])

    if suppliers_requiring_review:
        return {
            "supplier_eligibility_results": eligibility_results,
            "suppliers_requiring_review": suppliers_requiring_review,
            "rfq_drafting_status": "skipped",
            "workflow_status": "supplier_review_required",
            "current_agent": "rfq_drafting"
        }

    if not eligible_suppliers:
        return {
            "supplier_eligibility_results": eligibility_results,
            "suppliers_requiring_review": [],
            "rfq_drafting_status": "skipped",
            "workflow_status": "no_eligible_suppliers",
            "current_agent": "rfq_drafting"
        }

    result = run_rfq_drafting_agent(
        requirement=requirement,
        suppliers=eligible_suppliers
    )

    result_data = result.model_dump(mode="json")

    return {
        "supplier_eligibility_results": eligibility_results,
        "suppliers_requiring_review": [],
        "rfq_drafting_result": result_data,
        "rfq_drafts": result_data.get("rfq_drafts", []),
        "rfq_drafting_status": result_data.get("status"),
        "current_agent": "rfq_drafting",
        "workflow_status": (
            "pending_approval"
            if result_data.get("successful_drafts", 0) > 0
            else "rfq_drafting_failed"
        )
    }


def policy_guardrails_node(state: dict) -> dict:
    """Run Agent 11 against actual policy context for each RFQ draft."""
    from agents.policy_guardrails.agent import PolicyGuardrailsAgent

    drafts = state.get("rfq_drafts", [])
    policy_request = state.get("policy_evaluation_request")
    if isinstance(policy_request, dict):
        try:
            policy_request = PolicyEvaluationRequest.model_validate(
                policy_request
            )
        except ValidationError:
            policy_request = None
    policy_agent = state.get("policy_guardrails_agent") or PolicyGuardrailsAgent()
    results = []

    for draft in drafts:
        rfq_id = str(draft.get("rfq_id", ""))
        if policy_request is None:
            evaluation = PolicyEvaluationResult(
                decision=PolicyDecision.ESCALATE,
                risk_level=RiskLevel.MEDIUM,
                checks=[PolicyCheckResult(
                    check_name="policy_context",
                    status=CheckStatus.UNKNOWN,
                    reason=(
                        "Verified user and organization policy context is "
                        "unavailable; the RFQ cannot proceed automatically."
                    ),
                )],
                reasons=["Verified policy context is unavailable."],
                requires_human_review=True,
            )
        else:
            supplier = draft.get("supplier") or {}
            evaluation_request = policy_request.model_copy(update={
                "entity_type": "rfq",
                "entity_id": rfq_id,
                "supplier_status": supplier.get("status"),
            })
            evaluation = policy_agent.evaluate(evaluation_request)

        results.append({
            "rfq_id": rfq_id,
            "result": evaluation.model_dump(mode="json"),
        })

    decisions = [item["result"]["decision"] for item in results]
    if PolicyDecision.BLOCK.value in decisions:
        decision = PolicyDecision.BLOCK
    elif PolicyDecision.ESCALATE.value in decisions or not policy_request:
        decision = PolicyDecision.ESCALATE
    else:
        decision = PolicyDecision.ALLOW

    return {
        "policy_results": results,
        "policy_decision": decision.value,
        "policy_status": (
            "blocked" if decision == PolicyDecision.BLOCK
            else "human_review_required" if decision == PolicyDecision.ESCALATE
            else "passed"
        ),
        "workflow_status": (
            "policy_blocked" if decision == PolicyDecision.BLOCK
            else "policy_review_required" if decision == PolicyDecision.ESCALATE
            else state.get("workflow_status")
        ),
        "current_agent": "policy_guardrails",
    }
