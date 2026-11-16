import re
from datetime import date

from schemas.quotation import Quotation, DeliveryTimeUnit
from schemas.evaluation import ConstraintStatus


class ConstraintChecker:
    """Checks supplier quotations against mandatory RFQ requirements."""

    def check(
        self,
        quotation: Quotation,
        max_delivery_days: int = 20,
        min_warranty_years: int = 2,
        min_validity_days: int = 15,
        required_specs: list[str] | None = None,
    ) -> dict[str, ConstraintStatus]:

        results = {}

        # 1. Delivery time
        if quotation.delivery_time_days is None:
            results["delivery_time"] = ConstraintStatus.UNKNOWN

        elif quotation.delivery_time_unit == DeliveryTimeUnit.CALENDAR_DAYS:
            results["delivery_time"] = (
                ConstraintStatus.PASS
                if quotation.delivery_time_days <= max_delivery_days
                else ConstraintStatus.FAIL
            )

        else:
            # Working days cannot be directly compared with calendar days.
            results["delivery_time"] = ConstraintStatus.UNKNOWN

        # 2. Warranty
        if not quotation.warranty_period:
            results["warranty"] = ConstraintStatus.UNKNOWN
        else:
            warranty_text = quotation.warranty_period.lower()

            match = re.search(
                r"(\d+(?:\.\d+)?)\s*(year|yr|month|month[s]?)",
                warranty_text,
            )

            if not match:
                results["warranty"] = ConstraintStatus.UNKNOWN
            else:
                value = float(match.group(1))
                unit = match.group(2)

                warranty_years = (
                    value / 12 if unit.startswith("month") else value
                )

                results["warranty"] = (
                    ConstraintStatus.PASS
                    if warranty_years >= min_warranty_years
                    else ConstraintStatus.FAIL
                )

        # 3. Quotation validity
        if not quotation.issue_date or not quotation.valid_until:
            results["quotation_validity"] = ConstraintStatus.UNKNOWN
        else:
            validity_days = (
                quotation.valid_until - quotation.issue_date
            ).days

            results["quotation_validity"] = (
                ConstraintStatus.PASS
                if validity_days >= min_validity_days
                else ConstraintStatus.FAIL
            )

        
        
        # 4. Technical specifications
        if not required_specs:
            results["technical_specifications"] = ConstraintStatus.UNKNOWN
        else:
            available_text = " ".join(
                [
                    quotation.additional_terms or "",
                    *[
                        f"{item.product_name} {item.description or ''}"
                        for item in quotation.line_items
                    ],
                ]
            ).lower()

            # Specifications are only confirmed if explicitly present.
            # Missing information must remain UNKNOWN.
            missing_specs = [
                spec for spec in required_specs
                if spec.lower() not in available_text
            ]

            results["technical_specifications"] = (
                ConstraintStatus.UNKNOWN
                if missing_specs
                else ConstraintStatus.PASS
            )



        return results