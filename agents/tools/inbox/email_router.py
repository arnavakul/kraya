
from pydantic_models.email_message import EmailMessage
from pydantic_models.email_classification import EmailClassification
from pydantic_models.inbox_triage_result import InboxTriageResult
from pydantic_models.security_screening_result import SecurityScreeningResult


CONFIDENCE_THRESHOLD = 0.75


ROUTING_RULES = {
    "quotation": "quotation_processing",
    "question": "clarification_workflow",
    "rejection": "supplier_response_update",
    "follow_up": "follow_up_workflow",
    "spam": "quarantine",
    "out_of_office": "await_supplier_response",
    "suspicious": "security_review"
}


def route_email(
    email: EmailMessage,
    classification: EmailClassification,
    security_result: SecurityScreeningResult
) -> InboxTriageResult:

    # Validate that all three records belong to the same email.
    if not (
        email.email_id
        == security_result.email_id
        == getattr(classification, "email_id", email.email_id)
    ):
        raise ValueError("Email records do not match.")

    # Security screening always takes priority.
    if security_result.is_suspicious:

        return InboxTriageResult(
            email_id=email.email_id,
            category="suspicious",
            confidence=classification.confidence or 0.0,
            summary="Email flagged by security screening.",
            requires_human_review=True,
            security_flags=security_result.security_flags,
            routing_action="security_review"
        )

    # Suspicious classification also requires security review.
    if classification.category == "suspicious":

        return InboxTriageResult(
            email_id=email.email_id,
            category="suspicious",
            confidence=classification.confidence or 0.0,
            summary=classification.summary,
            requires_human_review=True,
            security_flags=[],
            routing_action="security_review"
        )

    # Low-confidence classifications must not enter normal workflows.
    if (
        classification.confidence is None
        or classification.confidence < CONFIDENCE_THRESHOLD
    ):

        return InboxTriageResult(
            email_id=email.email_id,
            category=classification.category,
            confidence=classification.confidence or 0.0,
            summary=classification.summary,
            requires_human_review=True,
            security_flags=[],
            routing_action="manual_review"
        )

    # Apply deterministic category-to-workflow mapping.
    routing_action = ROUTING_RULES[classification.category]

    return InboxTriageResult(
        email_id=email.email_id,
        category=classification.category,
        confidence=classification.confidence,
        summary=classification.summary,
        requires_human_review=False,
        security_flags=[],
        routing_action=routing_action
    )
