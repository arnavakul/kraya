
from pydantic_models.supplier_match import (
    SupplierMatch,
    MatchCriterion
)


def match_supplier_requirements(
    supplier,
    requirement: dict
) -> SupplierMatch:

    criteria = []
    warnings = []

    # 1. Product / Service
    product = requirement.get("product_service")

    if product:
        category_match = any(
            product.casefold() in category.casefold()
            or category.casefold() in product.casefold()
            for category in supplier.categories
        )

        name_match = product.casefold() in supplier.name.casefold()

        if category_match or name_match:
            criteria.append(
                MatchCriterion(
                    criterion="product_service",
                    required_value=product,
                    supplier_value=", ".join(supplier.categories),
                    status="matched",
                    explanation="Supplier category or name matches."
                )
            )
        else:
            criteria.append(
                MatchCriterion(
                    criterion="product_service",
                    required_value=product,
                    supplier_value=", ".join(supplier.categories),
                    status="not_matched",
                    explanation="No matching supplier category or name."
                )
            )

    # 2. Country
    country = requirement.get("country_code")

    if country:
        country_match = (
            supplier.country_code or ""
        ).upper() == country.upper()

        criteria.append(
            MatchCriterion(
                criterion="country_code",
                required_value=country,
                supplier_value=supplier.country_code,
                status="matched" if country_match else "not_matched",
                explanation=(
                    "Country matches."
                    if country_match
                    else "Country does not match."
                )
            )
        )

    # 3. Technical specifications
    specifications = requirement.get("specifications")

    if specifications:
        criteria.append(
            MatchCriterion(
                criterion="specifications",
                required_value=specifications,
                status="not_verifiable",
                explanation=(
                    "Supplier product specifications are not "
                    "available in the current database schema."
                )
            )
        )

    # 4. Quantity
    quantity = requirement.get("quantity")

    if quantity is not None:
        criteria.append(
            MatchCriterion(
                criterion="quantity",
                required_value=str(quantity),
                status="not_verifiable",
                explanation=(
                    "Supplier fulfilment capacity is not stored "
                    "in the current database schema."
                )
            )
        )

    # 5. Delivery location
    location = requirement.get("delivery_location")

    if location:
        criteria.append(
            MatchCriterion(
                criterion="delivery_location",
                required_value=location,
                status="not_verifiable",
                explanation=(
                    "Supplier delivery coverage is not available "
                    "in the current database schema."
                )
            )
        )

    statuses = [criterion.status for criterion in criteria]

    matched_count = statuses.count("matched")
    unmatched_count = statuses.count("not_matched")
    unverifiable_count = statuses.count("not_verifiable")

    if unmatched_count > 0:
        overall_status = "not_matched"

    elif unverifiable_count > 0:
        overall_status = "partially_matched" if matched_count else "insufficient_data"

    elif matched_count > 0:
        overall_status = "matched"

    else:
        overall_status = "insufficient_data"

    if unverifiable_count:
        warnings.append(
            f"{unverifiable_count} requirement(s) could not be verified."
        )

    return SupplierMatch(
        supplier_id=supplier.supplier_id,
        supplier_name=supplier.name,
        overall_status=overall_status,
        criteria=criteria,
        warnings=warnings
    )
