
from unittest.mock import patch

from orchestration.graph import procurement_graph

from pydantic_models.supplier_discovery_result import (
    SupplierDiscoveryResult
)

from pydantic_models.rfq import RFQDraftingResult


def get_valid_intake_result():
    return {
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


def create_supplier_assessment(
    name,
    overall_status,
    categories=None,
    verification_issues=None
):
    supplier_id = "38bf7f5f-6a8d-4e65-bd78-e71f10191abf"

    return {
        "supplier": {
            "supplier_id": supplier_id,
            "organization_id": "1c09b264-1bda-4641-9077-a549fa5162d8",
            "name": name,
            "status": "ACTIVE",
            "categories": categories or ["Laptops"]
        },
        "matching": {
            "supplier_id": supplier_id,
            "supplier_name": name,
            "overall_status": overall_status,
            "criteria": [],
            "warnings": []
        },
        "verification_evidence": [],
        "verification_issues": verification_issues or []
    }


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_reaches_rfq_drafting(
    mock_intake,
    mock_discovery,
    mock_rfq
):
    mock_intake.return_value = get_valid_intake_result()

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="completed",
        total_candidates=1,
        suppliers=[
            create_supplier_assessment(
                "Test Supplier",
                "matched"
            )
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
    assert result["supplier_eligibility_results"][0]["eligible"] is True


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_skips_rfq_when_no_suppliers(
    mock_intake,
    mock_discovery,
    mock_rfq
):
    mock_intake.return_value = get_valid_intake_result()

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


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_excludes_unmatched_supplier(
    mock_intake,
    mock_discovery,
    mock_rfq
):
    mock_intake.return_value = get_valid_intake_result()

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="completed",
        total_candidates=1,
        suppliers=[
            create_supplier_assessment(
                "Unmatched Supplier",
                "not_matched",
                categories=["Furniture"]
            )
        ]
    )

    result = procurement_graph.invoke({
        "user_input": "I need 20 laptops"
    })

    mock_rfq.assert_not_called()

    assert result["rfq_drafting_status"] == "skipped"
    assert result["workflow_status"] == "no_eligible_suppliers"
    assert result["supplier_eligibility_results"][0]["decision"] == "excluded"


@patch("orchestration.nodes.run_rfq_drafting_agent")
@patch("orchestration.nodes.run_supplier_discovery_agent")
@patch("orchestration.nodes.run_intake_agent")
def test_graph_requires_manual_review_for_partial_match(
    mock_intake,
    mock_discovery,
    mock_rfq
):
    mock_intake.return_value = get_valid_intake_result()

    mock_discovery.return_value = SupplierDiscoveryResult(
        status="completed",
        total_candidates=1,
        suppliers=[
            create_supplier_assessment(
                "Partially Matched Supplier",
                "partially_matched"
            )
        ]
    )

    result = procurement_graph.invoke({
        "user_input": "I need 20 laptops"
    })

    mock_rfq.assert_not_called()

    assert result["rfq_drafting_status"] == "skipped"
    assert result["workflow_status"] == "supplier_review_required"
    assert len(result["suppliers_requiring_review"]) == 1
    assert result["supplier_eligibility_results"][0]["decision"] == "manual_review"
