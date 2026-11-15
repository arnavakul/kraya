
from uuid import uuid4

from tools.dispatch.dispatch_models import EmailMessage
from tools.dispatch.mock_email_provider import MockEmailProvider


def create_test_message():
    return EmailMessage(
        rfq_id=uuid4(),
        recipient_email="supplier@example.com",
        subject="RFQ for Laptops",
        body="Please provide your quotation.",
        idempotency_key="test-key"
    )


def test_mock_provider_sends_email():
    provider = MockEmailProvider()

    result = provider.send(create_test_message())

    assert result.success is True
    assert result.provider == "mock"
    assert result.provider_message_id is not None
    assert len(provider.sent_messages) == 1


def test_mock_provider_records_recipient():
    provider = MockEmailProvider()

    message = create_test_message()
    provider.send(message)

    assert provider.sent_messages[0]["recipient"] == (
        "supplier@example.com"
    )


def test_mock_provider_simulates_failure():
    provider = MockEmailProvider(should_fail=True)

    result = provider.send(create_test_message())

    assert result.success is False
    assert result.provider == "mock"
    assert result.provider_message_id is None
    assert result.error is not None
    assert len(provider.sent_messages) == 0


def test_mock_provider_can_send_multiple_messages():
    provider = MockEmailProvider()

    result1 = provider.send(create_test_message())
    result2 = provider.send(create_test_message())

    assert result1.success is True
    assert result2.success is True
    assert len(provider.sent_messages) == 2
    assert (
        result1.provider_message_id
        != result2.provider_message_id
    )
