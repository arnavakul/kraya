
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field

from schemas.quotation import Quotation, ShippingStatus


class ValidationStatus(str, Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


@dataclass
class ValidationReport:
    status: ValidationStatus
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class FinancialValidator:
    """Validates financial calculations in supplier quotations."""

    def validate(self, quotation: Quotation) -> ValidationReport:

        errors = []
        warnings = []

        # 1. Validate line items.
        calculated_line_totals = []

        for index, item in enumerate(quotation.line_items, start=1):

            if item.unit_price is None or item.line_total is None:
                warnings.append(
                    f"Line item {index}: Unit price or line total is missing."
                )
                continue

            calculated_total = item.quantity * item.unit_price

            if calculated_total != item.line_total:
                errors.append(
                    f"Line item {index} ({item.product_name}): "
                    f"Expected {calculated_total}, "
                    f"but quotation states {item.line_total}."
                )

            calculated_line_totals.append(item.line_total)

        # 2. Validate subtotal.
        if quotation.subtotal is None:
            warnings.append("Subtotal is missing.")

        elif len(calculated_line_totals) == len(quotation.line_items):

            calculated_subtotal = sum(
                calculated_line_totals,
                Decimal("0")
            )

            if calculated_subtotal != quotation.subtotal:
                errors.append(
                    f"Subtotal mismatch: Expected {calculated_subtotal}, "
                    f"but quotation states {quotation.subtotal}."
                )

        # 3. Validate tax calculations.
        for tax in quotation.taxes:

            if tax.rate is None or tax.amount is None:
                warnings.append(
                    f"Tax information is incomplete for {tax.name}."
                )
                continue

            if quotation.subtotal is None:
                continue

            expected_tax = (
                quotation.subtotal * tax.rate / Decimal("100")
            )

            if expected_tax != tax.amount:
                errors.append(
                    f"{tax.name} mismatch: Expected {expected_tax}, "
                    f"but quotation states {tax.amount}."
                )

        # 4. Validate grand total.
        if quotation.grand_total is None:
            warnings.append("Grand total is missing.")

        elif quotation.subtotal is not None:

            total_tax = Decimal("0")
            tax_information_complete = True

            for tax in quotation.taxes:
                if tax.amount is None:
                    tax_information_complete = False
                    warnings.append(
                        f"Tax amount is missing for {tax.name}."
                    )
                else:
                    total_tax += tax.amount

            # Determine shipping amount.
            shipping = Decimal("0")
            shipping_known = True

            if quotation.shipping_status == ShippingStatus.AMOUNT:
                if quotation.shipping_cost is None:
                    shipping_known = False
                    warnings.append(
                        "Shipping status is amount, but cost is missing."
                    )
                else:
                    shipping = quotation.shipping_cost

            elif quotation.shipping_status == ShippingStatus.INCLUDED:
                shipping = Decimal("0")

            elif quotation.shipping_status == ShippingStatus.NOT_STATED:
                shipping_known = False
                warnings.append(
                    "Shipping charges are not stated. "
                    "Supplier clarification is required."
                )

            discount = quotation.discount or Decimal("0")

            calculated_grand_total = (
                quotation.subtotal
                + total_tax
                + shipping
                - discount
            )

            # Compare only when the required financial information exists.
            if shipping_known and tax_information_complete:
                if calculated_grand_total != quotation.grand_total:
                    errors.append(
                        f"Grand total mismatch: Expected "
                        f"{calculated_grand_total}, but quotation states "
                        f"{quotation.grand_total}."
                    )

        # 5. Determine final validation status.
        if errors:
            status = ValidationStatus.INVALID

        elif warnings:
            status = ValidationStatus.WARNING

        else:
            status = ValidationStatus.VALID

        return ValidationReport(
            status=status,
            errors=errors,
            warnings=warnings,
        )
