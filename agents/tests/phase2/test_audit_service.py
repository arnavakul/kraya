
from unittest.mock import Mock

from services.audit_service import AuditService


def test_audit_service_records_action():
    mock_repository = Mock()
    mock_repository.log_event.return_value = {"id": "audit-123"}

    service = AuditService(repository=mock_repository)

    result = service.record_action(
        organization_id="org-123",
        actor_user_id="user-123",
        action="SUPPLIER_APPROVED",
        entity_type="supplier",
        entity_id="supplier-123",
    )

    assert result == {"id": "audit-123"}
    mock_repository.log_event.assert_called_once()


def test_audit_service_passes_correlation_id():
    mock_repository = Mock()
    service = AuditService(repository=mock_repository)

    service.record_action(
        organization_id="org-123",
        actor_user_id="user-123",
        action="APPROVAL_REQUESTED",
        entity_type="supplier",
        entity_id="supplier-123",
        correlation_id="correlation-123",
    )

    call_kwargs = mock_repository.log_event.call_args.kwargs
    assert call_kwargs["correlation_id"] == "correlation-123"
