
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from tools.dispatch.dispatch_service import DispatchService
from tools.dispatch.dispatch_repository import (
    DuplicateDispatchError,
    DispatchStateError
)
from tools.dispatch.mock_email_provider import MockEmailProvider


def create_approved_rfq():
    return {
        "rfq_id": str(uuid4()),
        "status": "approved",
        "supplier": {
            "name": "Test Supplier",
            "contact_email": "supplier@example.com"
        },
        "email_subject": "RFQ for Laptops",
        "email_body": "Please provide your quotation."
    }


def create_repository():
    repository = MagicMock()

    repository.create_dispatch.return_value = {
        "dispatch_id": str(uuid4())
    }

    return repository


def test_dispatch_approved_rfq():
    repository = create_repository()
    provider = MockEmailProvider()

    service = DispatchService(provider, repository)

    result = service.dispatch_rfq(create_approved_rfq())

    assert result["status"] == "sent"
    assert len(provider.sent_messages) == 1

    repository.claim_dispatch.assert_called_once()
    repository.update_status.assert_called_once()


def test_unapproved_rfq_is_rejected():
    repository = create_repository()

    service = DispatchService(
        MockEmailProvider(),
        repository
    )

    rfq = create_approved_rfq()
    rfq["status"] = "pending_approval"

    with pytest.raises(ValueError, match="Only approved"):
        service.dispatch_rfq(rfq)

    repository.create_dispatch.assert_not_called()


def test_missing_recipient_is_rejected():
    repository = create_repository()

    service = DispatchService(
        MockEmailProvider(),
        repository
    )

    rfq = create_approved_rfq()
    rfq["supplier"]["contact_email"] = None

    with pytest.raises(ValueError, match="recipient email"):
        service.dispatch_rfq(rfq)


def test_duplicate_dispatch_is_prevented():
    repository = MagicMock()

    repository.create_dispatch.side_effect = DuplicateDispatchError()

    repository.get_by_idempotency_key.return_value = {
        "dispatch_id": "existing-dispatch",
        "status": "sent"
    }

    provider = MockEmailProvider()

    service = DispatchService(provider, repository)

    result = service.dispatch_rfq(create_approved_rfq())

    assert result["status"] == "duplicate"
    assert result["existing_status"] == "sent"
    assert len(provider.sent_messages) == 0

    repository.claim_dispatch.assert_not_called()


def test_provider_failure_is_recorded():
    repository = create_repository()
    provider = MockEmailProvider(should_fail=True)

    service = DispatchService(provider, repository)

    result = service.dispatch_rfq(create_approved_rfq())

    assert result["status"] == "failed"

    repository.update_status.assert_called_once_with(
        dispatch_id=repository.create_dispatch.return_value["dispatch_id"],
        status="failed",
        provider="mock",
        last_error="Simulated email delivery failure."
    )


def test_missing_email_body_is_rejected():
    repository = create_repository()

    service = DispatchService(
        MockEmailProvider(),
        repository
    )

    rfq = create_approved_rfq()
    rfq["email_body"] = ""

    with pytest.raises(ValueError, match="email body"):
        service.dispatch_rfq(rfq)

    repository.create_dispatch.assert_not_called()


def test_provider_exception_marks_dispatch_unknown():
    repository = create_repository()
    provider = MagicMock()

    provider.send.side_effect = TimeoutError(
        "Provider response timed out."
    )

    service = DispatchService(provider, repository)

    result = service.dispatch_rfq(create_approved_rfq())

    assert result["status"] == "unknown"

    repository.update_status.assert_called_once_with(
        dispatch_id=repository.create_dispatch.return_value["dispatch_id"],
        status="unknown",
        last_error="Provider response timed out."
    )


def test_claim_failure_prevents_email_send():
    repository = create_repository()

    repository.claim_dispatch.side_effect = DispatchStateError(
        "Already claimed."
    )

    provider = MockEmailProvider()

    service = DispatchService(provider, repository)

    result = service.dispatch_rfq(create_approved_rfq())

    assert result["status"] == "not_claimed"
    assert len(provider.sent_messages) == 0
