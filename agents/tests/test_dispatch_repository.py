
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from tools.dispatch.dispatch_repository import (
    DispatchRepository,
    DuplicateDispatchError,
    DispatchStateError
)


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_create_dispatch(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one.return_value = {
        "dispatch_id": "dispatch-001",
        "rfq_id": "rfq-001",
        "status": "pending"
    }

    repository = DispatchRepository()

    result = repository.create_dispatch({
        "rfq_id": "rfq-001",
        "recipient_email": "supplier@example.com",
        "subject": "RFQ",
        "idempotency_key": "test-key"
    })

    assert result["status"] == "pending"
    session.commit.assert_called_once()
    session.close.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_duplicate_dispatch_is_rejected(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.side_effect = IntegrityError(
        "INSERT", {}, Exception("Duplicate key")
    )

    repository = DispatchRepository()

    with pytest.raises(DuplicateDispatchError):
        repository.create_dispatch({
            "rfq_id": "rfq-001",
            "recipient_email": "supplier@example.com",
            "subject": "RFQ",
            "idempotency_key": "test-key"
        })

    session.rollback.assert_called_once()
    session.close.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_get_dispatch_by_idempotency_key(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "dispatch_id": "dispatch-001",
        "idempotency_key": "test-key"
    }

    repository = DispatchRepository()

    result = repository.get_by_idempotency_key("test-key")

    assert result["dispatch_id"] == "dispatch-001"
    session.close.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_claim_pending_dispatch(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "dispatch_id": "dispatch-001",
        "status": "sending",
        "attempt_count": 1
    }

    repository = DispatchRepository()

    result = repository.claim_dispatch("dispatch-001")

    assert result["status"] == "sending"
    assert result["attempt_count"] == 1
    session.commit.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_claim_already_claimed_dispatch_fails(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = None

    repository = DispatchRepository()

    with pytest.raises(DispatchStateError, match="cannot be claimed"):
        repository.claim_dispatch("dispatch-001")

    session.rollback.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_update_sending_dispatch_to_sent(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "dispatch_id": "dispatch-001",
        "status": "sent"
    }

    repository = DispatchRepository()

    result = repository.update_status(
        dispatch_id="dispatch-001",
        status="sent",
        provider="mock",
        provider_message_id="mock-123"
    )

    assert result["status"] == "sent"
    session.commit.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_invalid_state_transition_fails(mock_session_local):
    repository = DispatchRepository()

    with pytest.raises(ValueError, match="Use claim_dispatch"):
        repository.update_status(
            dispatch_id="dispatch-001",
            status="sending"
        )

    mock_session_local.assert_not_called()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_failed_dispatch_can_be_retried(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "dispatch_id": "dispatch-001",
        "status": "pending"
    }

    repository = DispatchRepository()

    result = repository.retry_failed_dispatch("dispatch-001")

    assert result["status"] == "pending"
    session.commit.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_unknown_dispatch_cannot_be_retried(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = None

    repository = DispatchRepository()

    with pytest.raises(DispatchStateError, match="Only failed"):
        repository.retry_failed_dispatch("dispatch-001")

    session.rollback.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_unknown_dispatch_can_be_reconciled(mock_session_local):
    session = MagicMock()
    mock_session_local.return_value = session

    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "dispatch_id": "dispatch-001",
        "status": "sent",
        "provider_message_id": "provider-123"
    }

    repository = DispatchRepository()

    result = repository.reconcile_dispatch(
        dispatch_id="dispatch-001",
        final_status="sent",
        provider_message_id="provider-123"
    )

    assert result["status"] == "sent"
    session.commit.assert_called_once()


@patch("tools.dispatch.dispatch_repository.SessionLocal")
def test_invalid_reconciliation_status_is_rejected(mock_session_local):
    repository = DispatchRepository()

    with pytest.raises(ValueError, match="Reconciliation status"):
        repository.reconcile_dispatch(
            dispatch_id="dispatch-001",
            final_status="sending"
        )

    mock_session_local.assert_not_called()
