
from uuid import uuid4

from pydantic_models.supplier_candidate import SupplierCandidate
from tools.supplier.supplier_matcher import match_supplier_requirements


def create_test_supplier():

    return SupplierCandidate(
        supplier_id=uuid4(),
        organization_id=uuid4(),
        name="Demo Supplier",
        status="ACTIVE",
        country_code="IN",
        categories=["Laptops"]
    )


def test_product_category_matching():

    supplier = create_test_supplier()

    result = match_supplier_requirements(
        supplier,
        {"product_service": "Laptop"}
    )

    assert result.overall_status == "matched"


def test_country_matching():

    supplier = create_test_supplier()

    result = match_supplier_requirements(
        supplier,
        {
            "product_service": "Laptop",
            "country_code": "IN"
        }
    )

    assert result.overall_status == "matched"


def test_specifications_not_verifiable():

    supplier = create_test_supplier()

    result = match_supplier_requirements(
        supplier,
        {
            "product_service": "Laptop",
            "specifications": "Intel i7, 16GB RAM"
        }
    )

    assert result.overall_status == "partially_matched"

    specification_criteria = [
        item for item in result.criteria
        if item.criterion == "specifications"
    ]

    assert specification_criteria[0].status == "not_verifiable"


def test_wrong_country():

    supplier = create_test_supplier()

    result = match_supplier_requirements(
        supplier,
        {
            "product_service": "Laptop",
            "country_code": "US"
        }
    )

    assert result.overall_status == "not_matched"
