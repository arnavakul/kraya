
from tools.supplier.supplier_repository import SupplierRepository


def test_get_all_suppliers():

    suppliers = SupplierRepository.get_all_suppliers()

    assert isinstance(suppliers, list)

    for supplier in suppliers:
        assert supplier.supplier_id is not None
        assert supplier.name
        assert isinstance(supplier.categories, list)


def test_get_supplier_by_id():

    suppliers = SupplierRepository.get_all_suppliers()

    if not suppliers:
        return

    supplier_id = str(suppliers[0].supplier_id)

    supplier = SupplierRepository.get_supplier_by_id(
        supplier_id
    )

    assert supplier is not None
    assert supplier.supplier_id == suppliers[0].supplier_id


def test_get_nonexistent_supplier():

    supplier = SupplierRepository.get_supplier_by_id(
        "00000000-0000-0000-0000-000000000000"
    )

    assert supplier is None

