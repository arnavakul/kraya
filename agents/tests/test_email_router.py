
import pytest

from pydantic_models.email_message import EmailMessage

from pydantic_models.email_classification import (
    EmailClassification
)

from pydantic_models.security_screening_result import (
    SecurityScreeningResult
)

from tools.inbox.email_router import route_email


def create_email():

    return EmailMessage(
        email_id="EMAIL-001",
        sender_email="supplier@example.com",
        subject="Supplier response",
        body="Please find our response."
    )


def create_classification(category, confidence=0.95):

    return EmailClassification(
        category=category,
        confidence=confidence,
        summary="Supplier email classification.",
        classification_source="llm"
    )


def create_security_result(suspicious=False):

    return SecurityScreeningResult(
        email_id="EMAIL-001",
        risk_level="high" if suspicious else "none",
        is_suspicious=suspicious,
        requires_human_review=suspicious,
        security_flags=["prompt_injection"] if suspicious else [],
        screening_summary="Security screening completed."
    )


@pytest.mark.parametrize(
    "category,expected_action",
    [
        ("quotation", "quotation_processing"),
        ("question", "clarification_workflow"),
        ("rejection", "supplier_response_update"),
        ("follow_up", "follow_up_workflow"),
        ("spam", "quarantine"),
        ("out_of_office", "await_supplier_response"),
        ("suspicious", "security_review"),
    ]
)
def test_category_routing(category, expected_action):

    result = route_email(
        create_email(),
        create_classification(category),
        create_security_result()
    )

    assert result.category == category
    assert result.routing_action == expected_action


def test_low_confidence_requires_manual_review():

    result = route_email(
        create_email(),
        create_classification("quotation", 0.50),
        create_security_result()
    )

    assert result.routing_action == "manual_review"
    assert result.requires_human_review is True


def test_suspicious_security_result_overrides_classification():

    result = route_email(
        create_email(),
        create_classification("quotation"),
        create_security_result(suspicious=True)
    )

    assert result.category == "suspicious"
    assert result.routing_action == "security_review"
    assert result.requires_human_review is True


def test_email_id_mismatch():

    security_result = create_security_result()
    security_result.email_id = "EMAIL-999"

    with pytest.raises(ValueError, match="do not match"):

        route_email(
            create_email(),
            create_classification("quotation"),
            security_result
        )


def test_confidence_boundary():

    result = route_email(
        create_email(),
        create_classification("quotation", 0.75),
        create_security_result()
    )

    assert result.routing_action == "quotation_processing"


def test_security_flags_are_preserved():

    result = route_email(
        create_email(),
        create_classification("quotation"),
        create_security_result(suspicious=True)
    )

    assert "prompt_injection" in result.security_flags
