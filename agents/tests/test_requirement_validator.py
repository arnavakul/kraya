
from tools.intake.requirement_validator import (
    validate_requirement
)

from pydantic_models.requirement_draft import (
    RequirementDraft
)


def test_valid_requirement():

    draft = RequirementDraft(
        product_service="Laptop",
        quantity=20,
        delivery_location="Kolkata"
    )

    result = validate_requirement(draft)

    assert result["valid"] is True


def test_missing_quantity():

    draft = RequirementDraft(
        product_service="Laptop",
        delivery_location="Kolkata"
    )

    result = validate_requirement(draft)

    assert result["valid"] is False

    assert "quantity" in result["missing_fields"]


def test_missing_location():

    draft = RequirementDraft(
        product_service="Laptop",
        quantity=20
    )

    result = validate_requirement(draft)

    assert "delivery_location" in result["missing_fields"]


def test_invalid_deadline():

    from datetime import date
    from datetime import timedelta

    draft = RequirementDraft(
        product_service="Laptop",
        quantity=20,
        delivery_location="Kolkata",
        delivery_deadline=date.today() - timedelta(days=1)
    )

    result = validate_requirement(draft)

    assert result["valid"] is False

    assert len(result["errors"]) > 0
