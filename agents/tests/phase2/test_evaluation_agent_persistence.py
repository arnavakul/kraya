
import pytest
from unittest.mock import MagicMock

from agents.evaluation.agent import EvaluationAgent
from schemas.quotation import Quotation, QuoteLineItem


@pytest.mark.asyncio
async def test_evaluate_and_save():
    mock_repository = MagicMock()

    agent = EvaluationAgent(
        evaluation_repository=mock_repository
    )

    quotation = Quotation(
        supplier_name="Demo Supplier",
        supplier_email="demo@example.com",
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Laptop",
                quantity=10,
                unit_price=50000,
                line_total=500000,
            )
        ],
        subtotal=500000,
        grand_total=500000,
        delivery_time_days=10,
        warranty_period="3 years",
        payment_terms="Net 30 days",
    )

    context = {
        "Demo Supplier": {
            "supplier_id": "supplier-123",
            "quote_id": "quote-123",
        }
    }

    result = await agent.evaluate_and_save(
        quotations=[quotation],
        evaluation_context=context,
        use_ml=False,
    )

    assert len(result.evaluations) == 1

    mock_repository.save_evaluation.assert_called_once()

    saved_record = (
        mock_repository.save_evaluation.call_args.kwargs
    )

    assert saved_record["supplier_id"] == "supplier-123"
    assert saved_record["quote_id"] == "quote-123"
    assert saved_record["baseline_score"] is None
