"""Safe handoff from validated quotation evaluation to Agent 9."""

from decimal import Decimal
from collections import Counter
from typing import Any

from pydantic import ValidationError

from schemas.approval import ApprovalAction, ApprovalRequest
from schemas.evaluation import EvaluationResult
from schemas.negotiation import (
    NegotiationAction,
    NegotiationContext,
    NegotiationPolicy,
    NegotiationResult,
    NegotiationStatus,
)
from schemas.policy import (
    CheckStatus,
    PolicyCheckResult,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskLevel,
)
from schemas.quotation import Quotation


REQUIRED_COMMERCIAL_LIMITS = (
    "target_price",
    "minimum_acceptable_price",
    "maximum_discount_percent",
    "minimum_quantity",
    "maximum_quantity",
    "maximum_delivery_days",
    "allowed_delivery_unit",
)


def _missing_limits(raw_policy: Any, policy: NegotiationPolicy) -> list[str]:
    if isinstance(raw_policy, dict):
        present = raw_policy.keys()
    else:
        present = getattr(policy, "model_fields_set", set())
    return [
        field for field in REQUIRED_COMMERCIAL_LIMITS
        if field not in present or getattr(policy, field) is None
    ]


def _policy_context(state: dict, source: dict, quotation: Quotation):
    raw_request = state.get("policy_evaluation_request")
    if isinstance(raw_request, dict):
        try:
            raw_request = PolicyEvaluationRequest.model_validate(raw_request)
        except ValidationError:
            raw_request = None

    if raw_request is None:
        return PolicyEvaluationResult(
            decision=PolicyDecision.ESCALATE,
            risk_level=RiskLevel.MEDIUM,
            checks=[PolicyCheckResult(
                check_name="policy_context",
                status=CheckStatus.UNKNOWN,
                reason=(
                    "Verified actor and organization context is unavailable "
                    "for negotiation."
                ),
            )],
            reasons=["Verified actor and organization context is unavailable."],
            requires_human_review=True,
        ), None

    policy_agent = state.get("policy_guardrails_agent")
    if policy_agent is None:
        from agents.policy_guardrails.agent import PolicyGuardrailsAgent

        policy_agent = PolicyGuardrailsAgent()

    request = raw_request.model_copy(update={
        "action": "NEGOTIATE_COUNTEROFFER",
        "entity_type": "supplier_message",
        "entity_id": source["email_id"],
        "untrusted_message": quotation.additional_terms,
    })
    return policy_agent.evaluate(request), raw_request


def _approval_record(
    state: dict,
    actor_context: PolicyEvaluationRequest | None,
    source_email_id: str,
    action: ApprovalAction,
    reason: str,
    evidence: list[str],
):
    if actor_context is None:
        return None

    approval_agent = state.get("approval_agent")
    if approval_agent is None:
        from agents.approval_audit.agent import ApprovalAuditAgent

        approval_agent = ApprovalAuditAgent()

    request = ApprovalRequest(
        organization_id=actor_context.organization_id,
        requester_user_id=actor_context.user_id,
        action=action,
        entity_type="supplier_message",
        entity_id=source_email_id,
        reason=reason,
        evidence=evidence,
    )
    record = approval_agent.create_approval_request(request)
    return record.model_dump(mode="json")


def _context_from_quote(quotation: Quotation) -> NegotiationContext | None:
    supplier_name = quotation.supplier_name
    current_price = quotation.grand_total
    if not supplier_name or current_price is None or current_price <= 0:
        return None

    total_quantity = sum(
        (item.quantity for item in quotation.line_items),
        start=Decimal("0"),
    )
    current_quantity = (
        int(total_quantity)
        if quotation.line_items and total_quantity == total_quantity.to_integral_value()
        else None
    )
    delivery_unit = getattr(quotation.delivery_time_unit, "value", quotation.delivery_time_unit)
    if (
        current_quantity is None
        or quotation.delivery_time_days is None
        or delivery_unit == "not_specified"
    ):
        return None

    return NegotiationContext(
        supplier_name=supplier_name,
        current_price=current_price,
        current_quantity=current_quantity,
        delivery_days=quotation.delivery_time_days,
        delivery_unit=delivery_unit,
        payment_terms=quotation.payment_terms,
        warranty=quotation.warranty_period,
        # No prior messages or instructions are available in the current
        # inbox result contract, so neither is inferred.
        conversation_history=[],
    )


def negotiation_node(state: dict) -> dict:
    """Propose internal counteroffers only for Agent 8 eligible suppliers."""
    evaluation = state.get("evaluation_result")
    triage_result = state.get("inbox_triage_result")
    if evaluation is None or triage_result is None:
        return {"negotiation_status": "skipped_missing_evaluation"}

    if isinstance(evaluation, dict):
        try:
            evaluation = EvaluationResult.model_validate(evaluation)
        except ValidationError:
            return {"negotiation_status": "skipped_invalid_evaluation"}

    evaluation_counts = Counter(
        item.supplier_name for item in evaluation.evaluations
    )
    eligible_evaluations = {
        item.supplier_name: item
        for item in evaluation.evaluations
        if item.eligible and evaluation_counts[item.supplier_name] == 1
    }
    eligible_names = set(eligible_evaluations)
    if not eligible_names:
        return {"negotiation_status": "skipped_no_eligible_suppliers"}

    completed_sources = [
        item for item in triage_result.quotation_processing_results
        if item.status == "completed" and item.quotation is not None
    ]
    supplier_counts = Counter(
        item.quotation.get("supplier_name") for item in completed_sources
    )
    sources = [
        item for item in completed_sources
        if item.quotation.get("supplier_name") in eligible_names
        and supplier_counts[item.quotation.get("supplier_name")] == 1
    ]
    if not sources:
        has_ambiguous = any(
            name in eligible_names and count > 1
            for name, count in supplier_counts.items()
        )
        return {
            "negotiation_status": (
                "skipped_ambiguous_supplier_quotes"
                if has_ambiguous
                else "skipped_no_matching_quotations"
            )
        }

    negotiation_agent = state.get("negotiation_agent")
    raw_policies = state.get("negotiation_policies", {})
    output = []
    approval_records = []
    any_review = False

    for source in sources:
        quotation = Quotation.model_validate(source.quotation)
        supplier_name = quotation.supplier_name
        try:
            policy_result, actor_context = _policy_context(
                state, source.model_dump(), quotation
            )
        except Exception as error:
            any_review = True
            output.append({
                "supplier_name": supplier_name,
                "email_id": source.email_id,
                "thread_id": source.thread_id,
                "supplier_evaluation": eligible_evaluations[
                    supplier_name
                ].model_dump(mode="json"),
                "status": "policy_review_required",
                "review_reasons": [f"Policy evaluation failed: {error}"],
                "approval_status": "not_created",
            })
            continue

        entry = {
            "supplier_name": supplier_name,
            "email_id": source.email_id,
            "thread_id": source.thread_id,
            "supplier_evaluation": eligible_evaluations[
                supplier_name
            ].model_dump(mode="json"),
            "policy_result": policy_result.model_dump(mode="json"),
            "negotiation_result": None,
            "approval_status": "not_required",
        }

        if policy_result.decision == PolicyDecision.BLOCK:
            entry["status"] = "policy_blocked"
            output.append(entry)
            continue

        if policy_result.decision == PolicyDecision.ESCALATE:
            any_review = True
            evidence = list(policy_result.reasons)
            try:
                approval = _approval_record(
                    state,
                    actor_context,
                    source.email_id,
                    ApprovalAction.POLICY_EXCEPTION,
                    "Policy review is required before negotiation.",
                    evidence,
                )
            except Exception as error:
                approval = None
                entry["approval_error"] = str(error)
            if approval is not None:
                approval_records.append(approval)
                entry["approval_record"] = approval
                entry["approval_status"] = approval["status"]
            else:
                entry["approval_status"] = (
                    "request_failed"
                    if entry.get("approval_error")
                    else "context_missing"
                )
            entry["status"] = "human_review_required"
            output.append(entry)
            continue

        raw_policy = raw_policies.get(supplier_name, {})
        try:
            policy = (
                raw_policy if isinstance(raw_policy, NegotiationPolicy)
                else NegotiationPolicy.model_validate(raw_policy)
            )
        except ValidationError as error:
            policy = NegotiationPolicy()
            missing_limits = [str(error)]
        else:
            missing_limits = _missing_limits(raw_policy, policy)

        context = _context_from_quote(quotation)
        if missing_limits or context is None:
            any_review = True
            reasons = list(missing_limits)
            if context is None:
                reasons.append(
                    "Validated quotation lacks price, quantity, or delivery "
                    "details required for negotiation."
                )
            entry.update({
                "status": "insufficient_information",
                "requires_human_review": True,
                "review_reasons": reasons,
            })
            output.append(entry)
            continue

        try:
            if negotiation_agent is None:
                from agents.negotiations.agent import NegotiationAgent

                negotiation_agent = NegotiationAgent()
            supplier_evaluation = eligible_evaluations[supplier_name]
            result: NegotiationResult = negotiation_agent.process_negotiation(
                context=context,
                policy=policy,
                supplier_evaluation=supplier_evaluation,
            )
        except Exception as error:
            any_review = True
            entry.update({
                "status": "negotiation_failed",
                "requires_human_review": True,
                "review_reasons": [f"Negotiation proposal generation failed: {error}"],
            })
            output.append(entry)
            continue
        entry["negotiation_result"] = result.model_dump(mode="json")
        if result.requires_human_approval:
            any_review = True
            try:
                approval = _approval_record(
                    state,
                    actor_context,
                    source.email_id,
                    ApprovalAction.SENSITIVE_ACTION,
                    "Human approval is required before a counteroffer may be considered.",
                    list(result.approval_reasons) + list(result.policy_violations),
                )
            except Exception as error:
                approval = None
                entry["approval_error"] = str(error)
            if approval is None:
                entry["approval_status"] = (
                    "request_failed"
                    if entry.get("approval_error")
                    else "context_missing"
                )
                entry["status"] = "human_review_required"
            else:
                approval_records.append(approval)
                entry["approval_record"] = approval
                entry["approval_status"] = approval["status"]
                entry["status"] = "approval_pending"
        else:
            entry["status"] = "proposal_ready_for_human_review"

        output.append(entry)

    return {
        "negotiation_results": output,
        "negotiation_approval_records": approval_records,
        "negotiation_status": (
            "human_review_required" if any_review else "completed"
        ),
        "current_agent": "negotiation",
    }
