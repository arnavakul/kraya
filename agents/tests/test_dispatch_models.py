
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tools.dispatch.dispatch_models import (
    EmailMessage,
    DispatchRecord
)

from tools.dispatch.idempotency import (
    generate_idempotency_key
)


def test_email_message_creation():
    rfq_id = uuid4()

    message = EmailMessage(
        rfq_id=rfq_id,
        recipient_email="supplier@example.com",
        subject="RFQ for Laptops",
        body="Please provide your quotation.",
        idempotency_key="test-key"
    )

    assert message.rfq_id == rfq_id
    assert message.recipient_email == "supplier@example.com"


def test_invalid_recipient_email_is_rejected():
    with pytest.raises(ValidationError):
        EmailMessage(
            rfq_id=uuid4(),
            recipient_email="invalid-email",
            subject="RFQ",
            body="Test body",
            idempotency_key="test-key"
        )


def test_empty_subject_is_rejected():
    with pytest.raises(ValidationError):
        EmailMessage(
            rfq_id=uuid4(),
            recipient_email="supplier@example.com",
            subject=" ",
            body="Test body",
            idempotency_key="test-key"
        )


def test_dispatch_record_defaults():
    record = DispatchRecord(
        rfq_id=uuid4(),
        recipient_email="supplier@example.com",
        subject="RFQ for Laptops",
        idempotency_key="test-key"
    )

    assert record.status == "pending"
    assert record.delivery_status == "unknown"
    assert record.attempt_count == 0
    assert record.provider_message_id is None


def test_idempotency_key_is_deterministic():
    rfq_id = str(uuid4())

    key1 = generate_idempotency_key(
        rfq_id,
        "supplier@example.com"
    )

    key2 = generate_idempotency_key(
        rfq_id,
        "supplier@example.com"
    )

    assert key1 == key2


def test_idempotency_key_normalizes_email():
    rfq_id = str(uuid4())

    key1 = generate_idempotency_key(
        rfq_id,
        "Supplier@Example.com"
    )

    key2 = generate_idempotency_key(
        rfq_id,
        "supplier@example.com"
    )

    assert key1 == key2


def test_different_rfqs_have_different_keys():
    key1 = generate_idempotency_key(
        str(uuid4()),
        "supplier@example.com"
    )

    key2 = generate_idempotency_key(
        str(uuid4()),
        "supplier@example.com"
    )

    assert key1 != key2
