
import pytest
from pydantic import ValidationError

from pydantic_models.email_message import EmailMessage
from pydantic_models.inbox_triage_result import InboxTriageResult


def test_email_message_creation():

    email = EmailMessage(
        email_id="EMAIL-001",
        sender_email="supplier@example.com",
        sender_name="ABC Suppliers",
        subject="Quotation for laptops",
        body="Please find our quotation attached."
    )

    assert email.email_id == "EMAIL-001"
    assert email.sender_email == "supplier@example.com"
    assert email.attachments == []


def test_email_message_requires_body():

    with pytest.raises(ValidationError):
        EmailMessage(
            email_id="EMAIL-001",
            sender_email="supplier@example.com",
            body=""
        )


def test_valid_triage_result():

    result = InboxTriageResult(
        email_id="EMAIL-001",
        category="quotation",
        confidence=0.96,
        summary="Supplier submitted a quotation.",
        routing_action="quotation_processing"
    )

    assert result.category == "quotation"
    assert result.confidence == 0.96


def test_invalid_category():

    with pytest.raises(ValidationError):
        InboxTriageResult(
            email_id="EMAIL-001",
            category="unknown",
            confidence=0.9,
            summary="Test",
            routing_action="quarantine"
        )


def test_invalid_confidence():

    with pytest.raises(ValidationError):
        InboxTriageResult(
            email_id="EMAIL-001",
            category="quotation",
            confidence=1.5,
            summary="Test",
            routing_action="quotation_processing"
        )


def test_suspicious_email_result():

    result = InboxTriageResult(
        email_id="EMAIL-002",
        category="suspicious",
        confidence=0.98,
        summary="Email contains suspicious instructions.",
        requires_human_review=True,
        security_flags=["prompt_injection"],
        routing_action="security_review"
    )

    assert result.requires_human_review is True
    assert result.routing_action == "security_review"
