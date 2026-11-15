
from uuid import uuid4

from pydantic_models.supplier_candidate import SupplierCandidate
from tools.supplier.supplier_matcher import match_supplier_requirements
from tools.supplier.supplier_verifier import verify_supplier
from tools.supplier.supplier_evidence import compile_supplier_evidence


def test_compile_supplier_evidence():

    supplier = SupplierCandidate(
        supplier_id=uuid4(),
        organization_id=uuid4(),
        name="Test Supplier",
        status="ACTIVE",
        country_code="IN",
        categories=["Laptops"],
        organization_type="SUPPLIER",
        organization_verified=True
    )

    requirement = {
        "product_service": "Laptop"
    }

    matching = match_supplier_requirements(
        supplier,
        requirement
    )

    evidence = verify_supplier(supplier)

    result = compile_supplier_evidence(
        supplier,
        matching,
        evidence
    )

    assert result.supplier.name == "Test Supplier"
    assert result.matching.overall_status == "matched"
    assert len(result.verification_evidence) == 8
    assert len(result.verification_issues) > 0
