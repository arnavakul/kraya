from agents.intake.agent import run_intake_agent
from agents.supplier_discovery.agent import run_supplier_discovery_agent
from agents.rfq_drafting.agent import run_rfq_drafting_agent
from tools.rfq.supplier_eligibility import evaluate_supplier_eligibility
from pydantic_models.supplier_candidate import SupplierCandidate


def intake_node(state: dict) -> dict:
    try:
        result = run_intake_agent(
            state.get("user_input", ""),
            state.get("requirement_draft"),
        )
        return {
            "requirement_draft": result.get("requirement_draft"),
            "requirement": result.get("requirement"),
            "missing_fields": result.get("missing_fields", []),
            "clarification_questions": result.get("clarification_questions", []),
            "intake_errors": result.get("errors", []),
            "intake_status": result.get("status", "failed"),
            "current_agent": "intake",
            "workflow_status": result.get("status", "failed"),
        }
    except Exception as error:
        return {"intake_status": "failed", "intake_errors": [str(error)],
                "errors": [str(error)], "workflow_status": "failed", "current_agent": "intake"}


def supplier_discovery_node(state: dict) -> dict:
    try:
        candidates_input = state.get("supplier_candidates_input")
        result = run_supplier_discovery_agent(
            state["requirement"],
            [SupplierCandidate.model_validate(item) for item in candidates_input]
            if candidates_input else None,
        )
        assessments = [item.model_dump(mode="json") for item in result.suppliers]
        decisions = []
        review = []
        eligible = []
        for assessment in assessments:
            decision = evaluate_supplier_eligibility(assessment)
            row = {"supplier_id": assessment["supplier"]["supplier_id"], **decision}
            decisions.append(row)
            if decision["eligible"]:
                eligible.append(assessment["supplier"])
            elif decision["decision"] == "manual_review":
                review.append(assessment)
        return {
            "supplier_discovery_result": result.model_dump(mode="json"),
            "supplier_candidates": eligible,
            "supplier_eligibility_results": decisions,
            "suppliers_requiring_review": review,
            "discovery_status": result.status,
            "workflow_status": ("supplier_review_required" if review and not eligible
                                else "no_eligible_suppliers" if not eligible
                                else "discovery_completed"),
            "current_agent": "supplier_discovery",
        }
    except Exception as error:
        return {"discovery_status": "failed", "errors": [str(error)],
                "workflow_status": "failed", "current_agent": "supplier_discovery"}


def rfq_drafting_node(state: dict) -> dict:
    candidates = state.get("supplier_candidates", [])
    if not candidates and state.get("supplier_candidates_input") is not None and state.get("suppliers_requiring_review"):
        candidates = [
            item["supplier"]
            for item in state["suppliers_requiring_review"]
            if item.get("matching", {}).get("overall_status") in ("matched", "partially_matched")
        ]
    if not candidates:
        return {"rfq_drafting_status": "skipped", "rfq_drafts": [],
                "workflow_status": state.get("workflow_status", "no_eligible_suppliers")}
    try:
        from pydantic_models.requirement import Requirement
        req = Requirement.model_validate(state["requirement"]) if isinstance(state.get("requirement"), dict) else state["requirement"]
        seen_names = set()
        deduped = []
        for c in candidates:
            c_name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else None)
            c_norm = c_name.strip().lower() if c_name else None
            if c_norm and c_norm in seen_names:
                continue
            if c_norm:
                seen_names.add(c_norm)
            deduped.append(c)

        validated_candidates = [
            SupplierCandidate.model_validate(c) if isinstance(c, dict) else c
            for c in deduped
        ]
        result = run_rfq_drafting_agent(req, validated_candidates)
        drafts = [item.model_dump(mode="json") for item in result.rfq_drafts]
        return {"rfq_drafting_result": result.model_dump(mode="json"),
                "rfq_drafts": drafts, "rfq_drafting_status": result.status,
                "workflow_status": "pending_approval" if result.status in ("completed", "partial") else result.status,
                "current_agent": "rfq_drafting", "errors": result.warnings}
    except Exception as error:
        return {"rfq_drafting_status": "failed", "errors": [str(error)],
                "workflow_status": "failed", "current_agent": "rfq_drafting"}
