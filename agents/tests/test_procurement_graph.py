
from unittest.mock import patch

from orchestration.graph import procurement_graph


@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_valid_requirement_runs_discovery(
    mock_intake,
    mock_discovery
):

    mock_intake.return_value = {
        "status": "validated",
        "requirement_draft": {},
        "requirement": {
            "product_service": "Laptop",
            "quantity": 20,
            "delivery_location": "Kolkata"
        },
        "missing_fields": [],
        "clarification_questions": [],
        "errors": []
    }

    from pydantic_models.supplier_discovery_result import (
        SupplierDiscoveryResult
    )

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="no_candidates",
        total_candidates=0,
        suppliers=[]
    )

    result = procurement_graph.invoke({
        "user_input": "I need 20 laptops"
    })

    mock_intake.assert_called_once()
    mock_discovery.assert_called_once()

    assert result["intake_status"] == "validated"
    assert result["discovery_status"] == "no_candidates"


@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_incomplete_requirement_stops_workflow(
    mock_intake,
    mock_discovery
):

    mock_intake.return_value = {
        "status": "needs_clarification",
        "requirement_draft": {},
        "requirement": None,
        "missing_fields": ["quantity"],
        "clarification_questions": [
            "What quantity do you require?"
        ],
        "errors": []
    }

    result = procurement_graph.invoke({
        "user_input": "I need laptops"
    })

    mock_intake.assert_called_once()
    mock_discovery.assert_not_called()

    assert result["intake_status"] == "needs_clarification"
    assert result["requirement"] is None
