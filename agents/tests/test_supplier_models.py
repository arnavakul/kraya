from uuid import uuid4

from pydantic_models.supplier_candidate import SupplierCandidate
from pydantic_models.verification_evidence import VerificationEvidence
from pydantic_models.supplier_discovery_result import SupplierDiscoveryResult


def test_supplier_candidate():

    supplier = SupplierCandidate(
        supplier_id=uuid4(),
        organization_id=uuid4(),
        name="Test Supplier",
        status="ACTIVE",
        categories=["Laptops"]
    )

    assert supplier.name == "Test Supplier"
    assert supplier.status == "ACTIVE"
    assert "Laptops" in supplier.categories


def test_verification_evidence():

    evidence = VerificationEvidence(
        field="company_name",
        value="Test Supplier",
        source="supplier_database",
        verification_status="unverified",
        checked_at="2026-11-15T10:00:00"
    )

    assert evidence.verification_status == "unverified"


def test_discovery_result():

    result = SupplierDiscoveryResult(
        status="completed",
        total_candidates=0
    )

    assert result.status == "completed"
    assert result.suppliers == []
