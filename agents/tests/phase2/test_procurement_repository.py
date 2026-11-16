
from unittest.mock import MagicMock

from repositories.procurement_repository import ProcurementRepository


def test_get_requests_filters_by_organization():
    mock_client = MagicMock()
    mock_query = MagicMock()

    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value.data = [
        {
            "id": "request-1",
            "organization_id": "org-123",
            "title": "Office Equipment",
            "status": "SUBMITTED",
        }
    ]

    repository = ProcurementRepository(client=mock_client)

    result = repository.get_requests("org-123")

    assert len(result) == 1
    assert result[0]["title"] == "Office Equipment"

    mock_client.table.assert_called_once_with("procurement_requests")
