
from langchain_core.messages import SystemMessage, HumanMessage

from tools.shared.llm import get_llm

from agents.inbox_triage.prompts import (
    EMAIL_CLASSIFICATION_SYSTEM_PROMPT
)

from pydantic_models.email_message import EmailMessage

from pydantic_models.email_classification import (
    EmailClassification
)

from pydantic_models.security_screening_result import (
    SecurityScreeningResult
)


def classify_email(
    email: EmailMessage,
    security_result: SecurityScreeningResult
) -> EmailClassification:

    # Ensure the screening result belongs to this email.
    if security_result.email_id != email.email_id:
        raise ValueError(
            "Email ID and security screening ID do not match."
        )

    # Security screening takes precedence over LLM classification.
    if security_result.is_suspicious:

        return EmailClassification(
            category="suspicious",
            confidence=None,
            summary=(
                "Email flagged by security screening. "
                "Normal classification was skipped."
            ),
            classification_source="security_rule"
        )

    # Initialize the existing shared LLM gateway.
    llm = get_llm(temperature=0)

    # Require structured Pydantic output.
    structured_llm = llm.with_structured_output(
        EmailClassification
    )

    # Keep email content separate from system instructions.
    messages = [
        SystemMessage(
            content=EMAIL_CLASSIFICATION_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=(
                "Classify this supplier email.\n\n"
                f"Subject:\n{email.subject}\n\n"
                f"Sender:\n{email.sender_email}\n\n"
                f"Body:\n{email.body}"
            )
        )
    ]

    result = structured_llm.invoke(messages)

    if not isinstance(result, EmailClassification):
        result = EmailClassification.model_validate(result)

    if result.classification_source != "llm":
        raise ValueError(
            "Unexpected classification source from LLM."
        )

    if result.confidence is None:
        raise ValueError(
            "LLM classification must include confidence."
        )

    return result
