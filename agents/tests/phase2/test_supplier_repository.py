
from unittest.mock import MagicMock

from repositories.supplier_repository import SupplierRepository


def test_get_suppliers_filters_by_organization():
    mock_client = MagicMock()
    mock_query = MagicMock()

    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.execute.return_value.data = [
        {"id": "supplier-1", "name": "Demo Supplier", "status": "ACTIVE"}
    ]

    repository = SupplierRepository(client=mock_client)

    result = repository.get_suppliers("org-123")

    assert len(result) == 1
    assert result[0]["name"] == "Demo Supplier"

    mock_client.table.assert_called_once_with("suppliers")
