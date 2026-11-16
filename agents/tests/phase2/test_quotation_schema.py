
from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.quotation import Quotation, QuoteLineItem


def test_valid_quotation():

    quotation = Quotation(
        supplier_name="ABC Technologies",
        quotation_number="QUO-001",
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Enterprise Server",
                quantity=Decimal("10"),
                unit_price=Decimal("75000"),
                line_total=Decimal("750000")
            )
        ],
        subtotal=Decimal("750000"),
        grand_total=Decimal("890000"),
        delivery_time_days=15,
        warranty_period="2 Years",
        payment_terms="50% Advance"
    )

    assert quotation.supplier_name == "ABC Technologies"
    assert quotation.grand_total == Decimal("890000")


def test_invalid_quantity():

    with pytest.raises(ValidationError):
        QuoteLineItem(
            product_name="Enterprise Server",
            quantity=Decimal("-5")
        )


def test_missing_optional_fields():

    quotation = Quotation(
        supplier_name="ABC Technologies"
    )

    assert quotation.supplier_email is None
    assert quotation.shipping_cost is None
    assert quotation.line_items == []
