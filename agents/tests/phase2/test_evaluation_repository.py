
from unittest.mock import MagicMock

from repositories.evaluation_repository import EvaluationRepository


def test_save_evaluation():
    mock_client = MagicMock()
    mock_query = MagicMock()

    mock_client.table.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.execute.return_value.data = [
        {
            "id": "evaluation-123",
            "supplier_id": "supplier-123",
            "quote_id": "quote-123",
            "composite_score": 88.5,
            "baseline_score": 75.0,
        }
    ]

    repository = EvaluationRepository(client=mock_client)

    result = repository.save_evaluation(
        supplier_id="supplier-123",
        quote_id="quote-123",
        composite_score=88.5,
        baseline_score=75.0,
        evaluation_id="evaluation-123",
    )

    assert result["composite_score"] == 88.5
    assert result["supplier_id"] == "supplier-123"

    mock_client.table.assert_called_once_with("evaluation_records")
