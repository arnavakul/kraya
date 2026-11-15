
from tools.supplier.supplier_repository import SupplierRepository


def test_inspect_supplier_search_data():

    suppliers = SupplierRepository.get_all_suppliers(
        active_only=True
    )

    print("\n========== SUPPLIER DATABASE DIAGNOSTICS ==========")
    print(f"Total active suppliers: {len(suppliers)}")

    for supplier in suppliers:

        print("\nSupplier:", supplier.name)
        print("Supplier ID:", supplier.supplier_id)
        print("Categories:", supplier.categories)
        print("Organization Type:", supplier.organization_type)
        print("Organization Verified:", supplier.organization_verified)
        print("Country:", supplier.country_code)
        print("Status:", supplier.status)

    print("\n====================================================")

    assert isinstance(suppliers, list)
