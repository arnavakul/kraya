
from agents.inbox_triage.agent import run_inbox_triage_agent

from orchestration.inbox_triage_state import InboxTriageState


def evaluation_node(state: InboxTriageState) -> dict:
    """Evaluate completed Agent 6 quotations with their approved RFQ context."""
    from agents.evaluation.agent import EvaluationAgent
    from pydantic_models.requirement import Requirement
    from schemas.quotation import Quotation
    import asyncio

    triage_result = state.get("inbox_triage_result")
    if triage_result is None:
        return {"evaluation_status": "skipped_no_inbox_result"}

    completed = [
        item for item in triage_result.quotation_processing_results
        if item.status == "completed" and item.quotation is not None
    ]
    if not completed:
        return {"evaluation_status": "skipped_no_validated_quotations"}

    handoff = state.get("approved_rfq_context")
    required_specs = None
    if handoff is not None:
        if not isinstance(handoff, dict):
            return {"evaluation_status": "skipped_invalid_rfq_context"}
        outbound_message_id = handoff.get("outbound_provider_message_id")
        supplier_email = str(handoff.get("supplier_email") or "").strip().lower()
        if not outbound_message_id or not supplier_email:
            return {"evaluation_status": "skipped_incomplete_rfq_context"}

        # Correlate by real email headers and the approved supplier. Unmatched
        # quotations continue through triage but cannot be evaluated here.
        completed = [
            item for item in completed
            if item.in_reply_to == outbound_message_id
            and item.sender_email.strip().lower() == supplier_email
        ]
        if not completed:
            return {"evaluation_status": "skipped_no_matching_approved_rfq_reply"}

        try:
            requirement = Requirement.model_validate(handoff.get("requirement"))
        except Exception:
            return {"evaluation_status": "skipped_invalid_rfq_requirement"}

        actual_requirements = [
            requirement.specifications,
            requirement.quality_requirements,
            *requirement.mandatory_constraints,
        ]
        required_specs = list(dict.fromkeys(
            item.strip() for item in actual_requirements
            if isinstance(item, str) and item.strip()
        )) or None

    try:
        quotations = [
            Quotation.model_validate(item.quotation) for item in completed
        ]
        agent = state.get("evaluation_agent") or EvaluationAgent()
        evaluation_kwargs = {
            "quotations": quotations,
            "ml_context": state.get("evaluation_ml_context", {}),
        }
        if handoff is not None:
            evaluation_kwargs["required_specs"] = required_specs
        result = asyncio.run(
            agent.evaluate_suppliers_with_ml(**evaluation_kwargs)
        )
        return {
            "evaluation_result": result,
            "evaluation_status": "completed",
            "evaluation_source_messages": [
                {
                    "email_id": item.email_id,
                    "thread_id": item.thread_id,
                    "in_reply_to": item.in_reply_to,
                    "supplier_email": item.sender_email,
                    "supplier_name": (
                        item.quotation.get("supplier_name")
                        if item.quotation else None
                    ),
                    "quotation_number": (
                        item.quotation.get("quotation_number")
                        if item.quotation else None
                    ),
                    "rfq_id": handoff.get("rfq_id") if handoff else None,
                    "supplier_id": handoff.get("supplier_id") if handoff else None,
                    "organization_id": handoff.get("organization_id") if handoff else None,
                }
                for item in completed
            ],
        }
    except Exception as error:
        return {
            "evaluation_status": "failed",
            "errors": state.get("errors", []) + [str(error)],
        }


def inbox_triage_node(state: InboxTriageState) -> dict:

    try:

        result = run_inbox_triage_agent(
            connector=state.get("connector"),
            repository=state.get("repository"),
            quote_extraction_agent=state.get(
                "quote_extraction_agent"
            ),
            supplier_intent_agent=state.get(
                "supplier_intent_agent"
            ),
            policy_guardrails_agent=state.get(
                "policy_guardrails_agent"
            ),
        )

        downstream_failures = [
            outcome.error
            for outcome in (
                result.quotation_processing_results
                + result.supplier_intent_results
            )
            if outcome.status == "failed" and outcome.error
        ]

        if result.total_failed == 0 and not downstream_failures:
            status = "completed"

        elif result.total_processed > 0 or result.total_skipped > 0:
            status = "partial"

        else:
            status = "failed"

        return {
            "inbox_triage_result": result,
            "inbox_triage_status": status,
            "errors": [
                item.error for item in result.failed_emails
            ] + downstream_failures
        }

    except Exception as error:

        return {
            "inbox_triage_status": "failed",
            "errors": [str(error)]
        }
