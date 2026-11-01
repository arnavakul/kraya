
from datetime import date

from pydantic_models.requirement_draft import (
    RequirementDraft
)


# Fields required before procurement can proceed
REQUIRED_FIELDS = [
    "product_service",
    "quantity",
    "delivery_location"
]


def validate_requirement(draft: RequirementDraft):

    missing_fields = []
    errors = []

    # 1. Check mandatory fields
    for field in REQUIRED_FIELDS:

        value = getattr(draft, field)

        if value is None:

            missing_fields.append(field)

        elif isinstance(value, str) and not value.strip():

            missing_fields.append(field)

    # 2. Validate quantity
    if draft.quantity is not None:

        if draft.quantity <= 0:
            errors.append("Quantity must be greater than zero")

    # 3. Validate budget
    if draft.budget is not None:

        if draft.budget <= 0:
            errors.append("Budget must be greater than zero")

    # 4. Validate delivery deadline
    if draft.delivery_deadline is not None:

        if draft.delivery_deadline < date.today():

            errors.append(
                "Delivery deadline cannot be in the past"
            )

    # 5. Validate currency when budget is specified
    if draft.budget is not None:

        if not draft.currency:

            missing_fields.append("currency")

    # 6. Remove duplicates
    missing_fields = list(dict.fromkeys(missing_fields))

    # Final validation result
    return {

        "valid": (
            len(missing_fields) == 0
            and len(errors) == 0
        ),

        "missing_fields": missing_fields,

        "errors": errors
    }
