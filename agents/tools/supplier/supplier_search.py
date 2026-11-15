
from tools.supplier.supplier_repository import SupplierRepository
from pydantic_models.supplier_candidate import SupplierCandidate


def search_suppliers(
    product_service: str,
    active_only: bool = True,
    country_code: str | None = None,
) -> list[SupplierCandidate]:

    if not product_service or not product_service.strip():
        raise ValueError("Product/service cannot be empty")

    suppliers = SupplierRepository.get_all_suppliers(
        active_only=active_only
    )

    search_term = product_service.strip().casefold()

    matching_suppliers = []

    for supplier in suppliers:

        categories = supplier.categories or []

        category_match = any(
            search_term in category.casefold()
            or category.casefold() in search_term
            for category in categories
        )

        name_match = search_term in supplier.name.casefold()

        if not (category_match or name_match):
            continue

        if country_code:
            if (supplier.country_code or "").upper() != country_code.upper():
                continue

        matching_suppliers.append(supplier)

    return matching_suppliers
