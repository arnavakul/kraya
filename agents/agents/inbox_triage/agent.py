
from tools.inbox.mock_email_connector import MockEmailConnector
from tools.inbox.email_connector import EmailConnector
from tools.inbox.security_screening import screen_email_security
from tools.inbox.email_classifier import classify_email
from tools.inbox.email_router import route_email
from tools.inbox.inbox_repository import InboxRepository
from agents.inbox_triage.handoffs import (
    process_clarification_message,
    process_quotation_message,
)

from pydantic_models.inbox_triage_result import (
    InboxTriageResult,
    InboxTriageRunResult,
    InboxProcessingFailure,
)


def run_inbox_triage_agent(
    connector: EmailConnector | None = None,
    repository: InboxRepository | None = None,
    quote_extraction_agent=None,
    supplier_intent_agent=None,
    policy_guardrails_agent=None,
) -> InboxTriageRunResult:
    """
    Fetch, claim, classify, route and persist incoming emails.

    Duplicate emails are skipped.
    Failed processing is recorded for controlled retries.
    """

    if connector is None:
        connector = MockEmailConnector()

    if repository is None:
        repository = InboxRepository()

    if policy_guardrails_agent is None:
        from agents.policy_guardrails.agent import PolicyGuardrailsAgent

        policy_guardrails_agent = PolicyGuardrailsAgent()

    emails = connector.fetch_emails()

    run_result = InboxTriageRunResult(
        total_fetched=len(emails)
    )

    for email in emails:

        # Stage 1: Atomically claim the email.
        try:
            claimed = repository.claim_email(email)

        except Exception as error:
            run_result.failed_emails.append(
                InboxProcessingFailure(
                    email_id=email.email_id,
                    stage="claim",
                    error=str(error)[:2000],
                )
            )
            continue

        # Existing email: do not process it again.
        if not claimed:
            run_result.skipped_email_ids.append(email.email_id)
            continue

        current_stage = "screening"

        try:
            # Stage 2: Security screening.
            security_result = screen_email_security(email)

            # Preserve the existing screening and add Agent 11's check
            # before classification or any LLM handoff.
            policy_check = policy_guardrails_agent.check_untrusted_message(
                f"{email.subject}\n{email.body}"
            )
            if policy_check.status.value != "pass":
                flags = list(security_result.security_flags)
                if policy_check.check_name not in flags:
                    flags.append(policy_check.check_name)
                security_result = security_result.model_copy(update={
                    "is_suspicious": True,
                    "requires_human_review": True,
                    "risk_level": (
                        "high" if policy_check.status.value == "fail"
                        else "medium"
                    ),
                    "security_flags": flags,
                    "screening_summary": policy_check.reason,
                })

            # Stage 3: Classification.
            current_stage = "classification"

            classification = classify_email(
                email=email,
                security_result=security_result,
            )

            # Stage 4: Deterministic routing.
            current_stage = "routing"

            triage_result = route_email(
                email=email,
                classification=classification,
                security_result=security_result,
            )

            if triage_result.routing_action == "quotation_processing":
                processing_result = process_quotation_message(
                    email=email,
                    quote_agent=quote_extraction_agent,
                )
                run_result.quotation_processing_results.append(
                    processing_result
                )
                if processing_result.requires_human_review:
                    triage_result = triage_result.model_copy(
                        update={"requires_human_review": True}
                    )

            elif triage_result.routing_action == "clarification_workflow":
                intent_result = process_clarification_message(
                    email=email,
                    intent_agent=supplier_intent_agent,
                )
                run_result.supplier_intent_results.append(intent_result)
                if intent_result.requires_human_review:
                    triage_result = triage_result.model_copy(
                        update={"requires_human_review": True}
                    )

            # Stage 5: Persist the result.
            current_stage = "persistence"

            saved = repository.complete_email(
                email_id=email.email_id,
                result=triage_result,
            )

            if not saved:
                raise RuntimeError(
                    "Email could not be marked completed. "
                    "Its processing state may have changed."
                )

            run_result.processed_emails.append(triage_result)

        except Exception as error:

            # Record failure without automatically retrying.
            try:
                repository.fail_email(
                    email_id=email.email_id,
                    error_message=str(error)[:2000],
                )

            except Exception as persistence_error:
                error = RuntimeError(
                    f"{error}; additionally, failure recording "
                    f"failed: {persistence_error}"
                )

            run_result.failed_emails.append(
                InboxProcessingFailure(
                    email_id=email.email_id,
                    stage=current_stage,
                    error=str(error)[:2000],
                )
            )

    run_result.total_processed = len(run_result.processed_emails)
    run_result.total_skipped = len(run_result.skipped_email_ids)
    run_result.total_failed = len(run_result.failed_emails)

    return run_result
