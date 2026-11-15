
from uuid import uuid4

from pydantic_models.supplier_candidate import SupplierCandidate
from tools.supplier.supplier_verifier import verify_supplier


def create_supplier():

    return SupplierCandidate(
        supplier_id=uuid4(),
        organization_id=uuid4(),
        name="Test Supplier",
        status="ACTIVE",
        country_code="IN",
        tax_id="TEST123",
        contact_email="test@example.com",
        contact_phone="1234567890",
        website_url="https://example.com",
        categories=["Laptops"],
        organization_name="Test Organization",
        organization_type="SUPPLIER",
        organization_verified=True
    )


def test_supplier_verification():

    supplier = create_supplier()

    evidence = verify_supplier(supplier)

    assert len(evidence) == 8

    organization_type = next(
        item for item in evidence
        if item.field == "organization_type"
    )

    assert organization_type.verification_status == "verified"


def test_unverified_organization():

    supplier = create_supplier()
    supplier.organization_verified = False

    evidence = verify_supplier(supplier)

    result = next(
        item for item in evidence
        if item.field == "organization_verified"
    )

    assert result.verification_status == "unverified"


def test_inconsistent_organization_type():

    supplier = create_supplier()
    supplier.organization_type = "BUYER"

    evidence = verify_supplier(supplier)

    result = next(
        item for item in evidence
        if item.field == "organization_type"
    )

    assert result.verification_status == "inconsistent"


def test_missing_tax_id():

    supplier = create_supplier()
    supplier.tax_id = None

    evidence = verify_supplier(supplier)

    result = next(
        item for item in evidence
        if item.field == "tax_id"
    )

    assert result.verification_status == "not_available"
