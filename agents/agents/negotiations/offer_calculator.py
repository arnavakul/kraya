
from decimal import Decimal
from typing import Optional

from schemas.negotiation import (
    NegotiationPolicy,
    NegotiationContext,
    CounterOffer,
)


class OfferCalculator:
    """
    Deterministic calculator for validating proposed negotiation terms.
    """

    def calculate_discount(
        self,
        current_price: Decimal,
        proposed_price: Decimal,
    ) -> Decimal:
        """Calculate discount percentage against current price."""

        if current_price <= 0:
            raise ValueError("Current price must be greater than zero.")

        if proposed_price < 0:
            raise ValueError("Proposed price cannot be negative.")

        discount = (
            (current_price - proposed_price)
            / current_price
        ) * Decimal("100")

        return discount.quantize(Decimal("0.01"))

    def validate_price(
        self,
        current_price: Optional[Decimal],
        proposed_price: Optional[Decimal],
        policy: NegotiationPolicy,
    ) -> list[str]:
        """Validate proposed price against buyer-approved limits."""

        violations = []

        if proposed_price is None:
            violations.append("Proposed price is missing.")
            return violations

        if proposed_price <= 0:
            violations.append("Proposed price must be greater than zero.")
            return violations

        if policy.minimum_acceptable_price is None:
            violations.append(
                "Minimum acceptable price is not configured."
            )
            return violations

        if proposed_price < policy.minimum_acceptable_price:
            violations.append(
                "Proposed price is below the minimum acceptable price."
            )

        if (
            current_price is not None
            and policy.maximum_discount_percent is not None
        ):
            if current_price <= 0:
                violations.append("Current price must be greater than zero.")
            else:
                discount = self.calculate_discount(
                    current_price,
                    proposed_price,
                )

                if discount > policy.maximum_discount_percent:
                    violations.append(
                        f"Proposed discount of {discount}% exceeds "
                        f"the maximum allowed discount of "
                        f"{policy.maximum_discount_percent}%."
                    )

        return violations

    def validate_quantity(
        self,
        proposed_quantity: Optional[int],
        policy: NegotiationPolicy,
    ) -> list[str]:
        """Validate proposed quantity against authorized limits."""

        violations = []

        if proposed_quantity is None:
            return violations

        if proposed_quantity < 1:
            violations.append("Quantity must be at least 1.")
            return violations

        if (
            policy.minimum_quantity is not None
            and proposed_quantity < policy.minimum_quantity
        ):
            violations.append(
                "Proposed quantity is below the authorized minimum."
            )

        if (
            policy.maximum_quantity is not None
            and proposed_quantity > policy.maximum_quantity
        ):
            violations.append(
                "Proposed quantity exceeds the authorized maximum."
            )

        return violations

    def validate_delivery(
        self,
        proposed_delivery_days: Optional[int],
        proposed_delivery_unit: Optional[str],
        policy: NegotiationPolicy,
    ) -> list[str]:
        """Validate proposed delivery time against policy."""

        violations = []

        if proposed_delivery_days is None:
            return violations

        if proposed_delivery_days < 1:
            violations.append("Delivery time must be at least 1 day.")
            return violations

        if policy.maximum_delivery_days is None:
            violations.append(
                "Maximum delivery time is not configured."
            )
            return violations

        if proposed_delivery_unit is None:
            violations.append(
                "Delivery time unit is missing; cannot validate delivery."
            )
            return violations

        if proposed_delivery_unit != policy.allowed_delivery_unit:
            violations.append(
                "Proposed delivery unit does not match the "
                "authorized delivery unit."
            )
            return violations

        if proposed_delivery_days > policy.maximum_delivery_days:
            violations.append(
                "Proposed delivery time exceeds the maximum allowed limit."
            )

        return violations

    def validate_offer(
        self,
        context: NegotiationContext,
        counter_offer: CounterOffer,
        policy: NegotiationPolicy,
    ) -> list[str]:
        """
        Validate all proposed numerical terms.

        Returns a list of policy violations.
        An empty list means no violations were detected.
        """

        violations = []

        # Price validation
        if counter_offer.proposed_price is not None:
            violations.extend(
                self.validate_price(
                    current_price=context.current_price,
                    proposed_price=counter_offer.proposed_price,
                    policy=policy,
                )
            )

        # Quantity validation
        violations.extend(
            self.validate_quantity(
                proposed_quantity=counter_offer.proposed_quantity,
                policy=policy,
            )
        )

        # Delivery validation
        violations.extend(
            self.validate_delivery(
                proposed_delivery_days=counter_offer.proposed_delivery_days,
                proposed_delivery_unit=counter_offer.proposed_delivery_unit,
                policy=policy,
            )
        )

        return violations
