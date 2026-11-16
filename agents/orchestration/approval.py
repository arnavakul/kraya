
from langgraph.types import interrupt
from schemas.approval import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
)
from pydantic import ValidationError
from schemas.policy import PolicyEvaluationRequest


def create_rfq_approval_requests_node(state: dict) -> dict:
    """Create Agent 12 records before entering the existing human pause."""
    drafts = state.get("rfq_drafts", [])
    policy_request = state.get("policy_evaluation_request")
    if isinstance(policy_request, dict):
        try:
            policy_request = PolicyEvaluationRequest.model_validate(
                policy_request
            )
        except ValidationError:
            policy_request = None

    if not drafts:
        return {
            "approval_records": [],
            "approval_request_status": "not_required",
        }

    # These are existing required fields in PolicyEvaluationRequest and
    # ApprovalRequest. Missing identity must never be inferred.
    if policy_request is None or not policy_request.organization_id or not policy_request.user_id:
        return {
            "approval_records": [],
            "approval_request_status": "context_missing",
            "approval_status": "human_review_required",
            "workflow_status": "approval_context_missing",
            "current_agent": "approval_request",
        }

    approval_agent = state.get("approval_agent")
    if approval_agent is None:
        from agents.approval_audit.agent import ApprovalAuditAgent

        approval_agent = ApprovalAuditAgent()

    policy_by_rfq = {
        item["rfq_id"]: item["result"]
        for item in state.get("policy_results", [])
    }
    records = []
    try:
        for draft in drafts:
            rfq_id = str(draft["rfq_id"])
            policy_result = policy_by_rfq.get(rfq_id, {})
            reasons = list(policy_result.get("reasons", []))
            if not reasons:
                reasons = ["RFQ dispatch requires human review."]
            requested_action = state.get("approval_action")
            try:
                action = (
                    ApprovalAction(requested_action)
                    if requested_action is not None
                    else ApprovalAction.SUPPLIER_SELECTION
                )
            except ValueError:
                return {
                    "approval_records": records,
                    "approval_request_status": "invalid_action",
                    "approval_status": "human_review_required",
                    "workflow_status": "approval_request_failed",
                    "errors": state.get("errors", []) + [
                        "Approval action is not supported by the existing contract."
                    ],
                    "current_agent": "approval_request",
                }
            request = ApprovalRequest(
                organization_id=policy_request.organization_id,
                requester_user_id=policy_request.user_id,
                action=action,
                entity_type="rfq",
                entity_id=rfq_id,
                reason=" ".join(reasons),
                evidence=reasons,
            )
            record = approval_agent.create_approval_request(request)
            records.append(record.model_dump(mode="json"))
    except Exception as error:
        # Do not route partially created requests to a decision or dispatch.
        return {
            "approval_records": records,
            "approval_request_status": "failed",
            "approval_status": "human_review_required",
            "workflow_status": "approval_request_failed",
            "errors": state.get("errors", []) + [str(error)],
            "current_agent": "approval_request",
        }

    return {
        "approval_records": records,
        "approval_request_status": "pending",
        "approval_status": "pending",
        "workflow_status": "pending_approval",
        "current_agent": "approval_request",
    }


def rfq_approval_node(state: dict, approval_agent=None) -> dict:
    rfq_drafts = state.get("rfq_drafts", [])

    if not rfq_drafts:
        return {
            "approval_status": "not_required",
            "workflow_status": "no_rfqs_to_approve"
        }

    records = state.get("approval_records", [])
    record_by_rfq = {
        item.get("entity_id"): item for item in records
        if item.get("entity_type") == "rfq"
    }
    expected_ids = {str(draft["rfq_id"]) for draft in rfq_drafts}
    if set(record_by_rfq) != expected_ids:
        return {
            "approval_status": "human_review_required",
            "workflow_status": "approval_context_missing",
            "errors": state.get("errors", []) + [
                "A matching Agent 12 approval request is required for every RFQ."
            ],
            "current_agent": "rfq_approval",
        }

    for record in record_by_rfq.values():
        if record.get("status") != ApprovalStatus.PENDING.value:
            return {
                "approval_status": "human_review_required",
                "workflow_status": "approval_not_pending",
                "current_agent": "rfq_approval",
            }

    # Pause execution and request human decisions.
    decisions = interrupt({
        "type": "rfq_approval_required",
        "message": "Review each RFQ and approve or reject it.",
        "rfq_drafts": [
            {
                "rfq_id": draft["rfq_id"],
                "approval_id": record_by_rfq[str(draft["rfq_id"])]["id"],
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
        reviewer_user_id = item.get("reviewer_user_id")

        if decision not in ("approve", "reject"):
            raise ValueError(f"Invalid decision for RFQ {rfq_id}.")

        if rfq_id in decision_map:
            raise ValueError(f"Duplicate decision for RFQ {rfq_id}.")

        if not reviewer_user_id or not str(reviewer_user_id).strip():
            raise ValueError(
                f"A reviewer_user_id is required for RFQ {rfq_id}."
            )
        decision_map[rfq_id] = (decision, str(reviewer_user_id), item.get("comments"))

    expected_ids = {draft["rfq_id"] for draft in rfq_drafts}

    if set(decision_map) != expected_ids:
        raise ValueError(
            "A decision must be submitted for every RFQ, "
            "with no unknown RFQ IDs."
        )

    updated_drafts = []
    approved_rfq_contexts = []
    approved_count = 0
    rejected_count = 0
    if approval_agent is None:
        from agents.approval_audit.agent import ApprovalAuditAgent

        approval_agent = ApprovalAuditAgent()

    for draft in rfq_drafts:
        updated_draft = draft.copy()

        decision, reviewer_user_id, comments = decision_map[draft["rfq_id"]]

        approval_record = record_by_rfq[str(draft["rfq_id"])]
        status = (
            ApprovalStatus.APPROVED
            if decision == "approve"
            else ApprovalStatus.REJECTED
        )
        processed = approval_agent.process_decision(
            decision=ApprovalDecision(
                approval_id=approval_record["id"],
                reviewer_user_id=reviewer_user_id,
                status=status,
                comments=comments,
            ),
            organization_id=approval_record["organization_id"],
        )
        if processed.status != status:
            raise ValueError("Approval decision was not persisted as requested.")

        if decision == "approve":
            updated_draft["status"] = "approved"
            approved_count += 1

            policy_context = state.get("policy_evaluation_request")
            if isinstance(policy_context, dict):
                try:
                    policy_context = PolicyEvaluationRequest.model_validate(
                        policy_context
                    )
                except ValidationError:
                    policy_context = None

            approval_context = {
                "rfq_id": str(draft["rfq_id"]),
                "requirement": draft.get("requirement"),
                "supplier": draft.get("supplier"),
                "organization_id": record_by_rfq[
                    str(draft["rfq_id"])
                ].get("organization_id"),
                "approval_id": record_by_rfq[
                    str(draft["rfq_id"])
                ].get("id"),
                "reviewer_user_id": reviewer_user_id,
            }
            if policy_context is not None:
                approval_context["requester_user_id"] = policy_context.user_id
                approval_context["policy_evaluation_request"] = (
                    policy_context.model_dump(mode="json")
                )
            for optional_id in ("procurement_request_id", "correlation_id"):
                value = state.get(optional_id)
                if value is not None:
                    approval_context[optional_id] = value
            approved_rfq_contexts.append(approval_context)
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
        "approved_rfq_contexts": approved_rfq_contexts,
        "current_agent": "rfq_approval"
    }

