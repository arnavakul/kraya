
from datetime import date

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate
from tools.rfq.rfq_template import build_rfq_template


def test_rfq_template_preserves_requirements():

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
        contact_email="supplier@example.com",
        status="ACTIVE",
        categories=["Laptops"]
    )

    template = build_rfq_template(requirement, supplier)

    assert template["supplier_name"] == "Test Supplier"
    assert template["product_service"] == "Laptop"
    assert template["quantity"] == 20
    assert template["specifications"] == (
        "Intel i7, 16GB RAM, 512GB SSD"
    )
    assert template["delivery_location"] == "Kolkata"
    assert template["budget"] == 2000000
    assert template["mandatory_constraints"] == [
        "3-year warranty"
    ]

