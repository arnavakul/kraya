
from datetime import date

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate
from pydantic_models.rfq import RFQDraft, RFQDraftingResult


def test_rfq_draft_model():

    requirement = Requirement(
        product_service="Laptop",
        quantity=20,
        specifications="Intel i7, 16GB RAM, 512GB SSD",
        delivery_location="Kolkata",
        delivery_deadline=date(2026, 12, 15),
        budget=2000000,
        mandatory_constraints=["3-year warranty"]
    )

    supplier = SupplierCandidate(
        supplier_id="38bf7f5f-6a8d-4e65-bd78-e71f10191abf",
        organization_id="1c09b264-1bda-4641-9077-a549fa5162d8",
        name="Test Supplier",
        status="ACTIVE",
        categories=["Laptops"]
    )

    rfq = RFQDraft(
        requirement=requirement,
        supplier=supplier,
        email_subject="Request for Quotation - 20 Laptops",
        email_body="Please provide your quotation for the specified laptops."
    )

    assert rfq.status == "draft"
    assert rfq.requirement.quantity == 20
    assert rfq.supplier.name == "Test Supplier"
    assert rfq.rfq_id is not None


def test_rfq_drafting_result():

    result = RFQDraftingResult(
        status="completed",
        total_suppliers=2,
        successful_drafts=2
    )

    assert result.total_suppliers == 2
    assert result.successful_drafts == 2
    assert result.failed_drafts == 0
    assert result.rfq_drafts == []
