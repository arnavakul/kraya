
from tools.supplier.supplier_search import search_suppliers


def test_search_suppliers():

    results = search_suppliers(
        product_service="demoCommercial"
    )

    assert isinstance(results, list)

    for supplier in results:
        assert supplier.status == "ACTIVE"
        assert "demoCommercial" in supplier.categories


def test_search_with_nonexistent_category():

    results = search_suppliers(
        product_service="nonexistent_category_xyz"
    )

    assert results == []


def test_search_empty_product():

    try:
        search_suppliers(product_service="")
        assert False, "Expected ValueError"

    except ValueError:
        assert True


def test_search_with_country_filter():

    results = search_suppliers(
        product_service="demoCommercial",
        country_code="IN"
    )

    for supplier in results:
        assert supplier.country_code == "IN"
