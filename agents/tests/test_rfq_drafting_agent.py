
from datetime import date
from unittest.mock import patch

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate
from agents.rfq_drafting.agent import run_rfq_drafting_agent


def create_test_requirement():
    return Requirement(
        product_service="Laptop",
        quantity=20,
        specifications="Intel i7, 16GB RAM, 512GB SSD",
        delivery_location="Kolkata",
        delivery_deadline=date(2026, 12, 15),
        budget=2000000,
        mandatory_constraints=["3-year warranty"]
    )


def create_test_supplier():
    return SupplierCandidate(
        supplier_id="38bf7f5f-6a8d-4e65-bd78-e71f10191abf",
        organization_id="1c09b264-1bda-4641-9077-a549fa5162d8",
        name="Test Supplier",
        contact_email="supplier@example.com",
        status="ACTIVE",
        categories=["Laptops"]
    )


@patch("agents.rfq_drafting.agent.draft_rfq_email")
def test_rfq_agent_generates_draft(mock_email):

    mock_email.return_value = {
        "email_subject": "RFQ - 20 Laptops",
        "opening_message": "Dear Supplier, please review our procurement requirement.",
        "closing_message": "Please submit your quotation at your earliest convenience."
    }

    result = run_rfq_drafting_agent(
        requirement=create_test_requirement(),
        suppliers=[create_test_supplier()]
    )

    print("\nRFQ RESULT:", result.model_dump(mode="json"))
    print("\nWARNINGS:", result.warnings)

    assert result.status == "completed"
    assert result.total_suppliers == 1
    assert result.successful_drafts == 1
    assert result.failed_drafts == 0

    assert result.rfq_drafts[0].status == "pending_approval"


@patch("agents.rfq_drafting.agent.draft_rfq_email")
def test_rfq_agent_handles_generation_failure(mock_email):

    mock_email.side_effect = Exception("Gemini API unavailable")

    result = run_rfq_drafting_agent(
        requirement=create_test_requirement(),
        suppliers=[create_test_supplier()]
    )

    assert result.status == "failed"
    assert result.successful_drafts == 0
    assert result.failed_drafts == 1
    assert len(result.warnings) == 1


def test_rfq_agent_handles_empty_supplier_list():

    result = run_rfq_drafting_agent(
        requirement=create_test_requirement(),
        suppliers=[]
    )

    assert result.status == "failed"
    assert result.total_suppliers == 0

