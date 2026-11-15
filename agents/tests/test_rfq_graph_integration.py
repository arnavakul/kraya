
from unittest.mock import patch

from orchestration.graph import procurement_graph

from pydantic_models.supplier_discovery_result import (
    SupplierDiscoveryResult
)

from pydantic_models.rfq import RFQDraftingResult


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_reaches_rfq_drafting(
    mock_intake,
    mock_discovery,
    mock_rfq
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

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="completed",
        total_candidates=1,
        suppliers=[
            {
                "supplier": {
                    "supplier_id": "38bf7f5f-6a8d-4e65-bd78-e71f10191abf",
                    "organization_id": "1c09b264-1bda-4641-9077-a549fa5162d8",
                    "name": "Test Supplier",
                    "status": "ACTIVE",
                    "categories": ["Laptops"]
                },
                "matching": {
                    "supplier_id": "38bf7f5f-6a8d-4e65-bd78-e71f10191abf",
                    "supplier_name": "Test Supplier",
                    "overall_status": "matched",
                    "criteria": [],
                    "warnings": []
                },
                "verification_evidence": [],
                "verification_issues": []
            }
        ]
    )

    mock_rfq.return_value = RFQDraftingResult(
        status="completed",
        total_suppliers=1,
        successful_drafts=1
    )

    result = procurement_graph.invoke({
        "user_input": "I need 20 laptops"
    })

    mock_rfq.assert_called_once()

    assert result["intake_status"] == "validated"
    assert result["discovery_status"] == "completed"
    assert result["rfq_drafting_status"] == "completed"
    assert result["workflow_status"] == "pending_approval"


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_skips_rfq_when_no_suppliers(
    mock_intake,
    mock_discovery,
    mock_rfq
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

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="no_candidates",
        total_candidates=0,
        suppliers=[]
    )

    result = procurement_graph.invoke({
        "user_input": "I need 20 laptops"
    })

    mock_rfq.assert_not_called()

    assert result["discovery_status"] == "no_candidates"
    assert "rfq_drafting_status" not in result
