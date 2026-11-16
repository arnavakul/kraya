
from decimal import Decimal

from schemas.quotation import (
    Quotation,
    QuoteLineItem,
    TaxComponent,
    ShippingStatus,
)

from services.financial_validator import (
    FinancialValidator,
    ValidationStatus,
)


validator = FinancialValidator()


def create_quotation(
    line_total="750000",
    subtotal="750000",
    grand_total="890000",
    shipping_status=ShippingStatus.AMOUNT,
    shipping_cost="5000",
    tax_amount="135000",
):
    """Creates a reusable quotation for testing."""

    return Quotation(
        supplier_name="ABC Technologies",
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Enterprise Server",
                quantity=Decimal("10"),
                unit_price=Decimal("75000"),
                line_total=Decimal(line_total),
            )
        ],
        subtotal=Decimal(subtotal),
        taxes=[
            TaxComponent(
                name="GST",
                rate=Decimal("18"),
                amount=Decimal(tax_amount) if tax_amount is not None else None,
            )
        ],
        shipping_cost=(
            Decimal(shipping_cost)
            if shipping_cost is not None
            else None
        ),
        shipping_status=shipping_status,
        discount=Decimal("0"),
        grand_total=Decimal(grand_total),
    )


def test_valid_quotation():
    quotation = create_quotation()

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.VALID


def test_missing_shipping_returns_warning():
    quotation = create_quotation(
        shipping_status=ShippingStatus.NOT_STATED,
        shipping_cost=None,
    )

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.WARNING
    assert len(report.warnings) > 0


def test_incorrect_line_total_returns_invalid():
    quotation = create_quotation(
        line_total="740000",
        subtotal="740000",
        grand_total="880000",
    )

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.INVALID
    assert len(report.errors) > 0


def test_incorrect_grand_total_returns_invalid():
    quotation = create_quotation(
        grand_total="900000",
    )

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.INVALID


def test_multiple_line_items_validate_subtotal():
    quotation = Quotation(
        supplier_name="CloudServe Technologies",
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Enterprise Server",
                quantity=Decimal("10"),
                unit_price=Decimal("78000"),
                line_total=Decimal("780000"),
            ),
            QuoteLineItem(
                product_name="Rack Mounting Kit",
                quantity=Decimal("2"),
                unit_price=Decimal("15000"),
                line_total=Decimal("30000"),
            ),
        ],
        subtotal=Decimal("810000"),
        taxes=[
            TaxComponent(
                name="GST",
                rate=Decimal("18"),
                amount=Decimal("145800"),
            )
        ],
        shipping_cost=None,
        shipping_status=ShippingStatus.INCLUDED,
        discount=Decimal("10000"),
        grand_total=Decimal("945800"),
    )

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.VALID


def test_missing_tax_amount_returns_warning():
    quotation = create_quotation(tax_amount=None)

    report = validator.validate(quotation)

    assert report.status == ValidationStatus.WARNING

def test_incorrect_tax_amount_returns_invalid():
    quotation = create_quotation(
        tax_amount="125000"
    )

    report = validator.validate(quotation)

    print("\nACTUAL ERRORS:", report.errors)

    assert report.status == ValidationStatus.INVALID
    assert any("GST mismatch" in error for error in report.errors)