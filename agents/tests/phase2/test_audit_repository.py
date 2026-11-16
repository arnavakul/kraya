
from unittest.mock import Mock

from repositories.audit_repository import AuditRepository


def test_log_event_inserts_audit_record():
    mock_client = Mock()
    mock_response = Mock()

    expected_record = {
        "id": "audit-123",
        "action": "SUPPLIER_APPROVED",
        "result": "SUCCESS",
    }

    mock_response.data = [expected_record]

    mock_client.table.return_value.insert.return_value.execute.return_value = (
        mock_response
    )

    repository = AuditRepository(client=mock_client)

    result = repository.log_event(
        organization_id="org-123",
        actor_user_id="user-123",
        action="SUPPLIER_APPROVED",
        entity_type="supplier",
        entity_id="supplier-123",
    )

    assert result == expected_record

    mock_client.table.assert_called_once_with("audit_events")
    mock_client.table.return_value.insert.assert_called_once()


def test_log_event_raises_error_when_insert_fails():
    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = []

    mock_client.table.return_value.insert.return_value.execute.return_value = (
        mock_response
    )

    repository = AuditRepository(client=mock_client)

    import pytest

    with pytest.raises(RuntimeError):
        repository.log_event(
            organization_id="org-123",
            actor_user_id="user-123",
            action="SUPPLIER_APPROVED",
            entity_type="supplier",
            entity_id="supplier-123",
        )
