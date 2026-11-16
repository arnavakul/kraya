
from decimal import Decimal

from schemas.negotiation import (
    NegotiationPolicy,
    NegotiationContext,
    CounterOffer,
)


class ApprovalChecker:
    """
    Determines whether a negotiation proposal requires human approval.

    This component never sends messages or authorizes commercial commitments.
    """

    def check_approval_required(
        self,
        context: NegotiationContext,
        counter_offer: CounterOffer,
        policy: NegotiationPolicy,
        policy_violations: list[str] | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Returns:
            (requires_approval, approval_reasons)
        """

        approval_reasons = []

        # Rule 1: Every counteroffer requires approval by default.
        if policy.requires_human_approval:
            approval_reasons.append(
                "Buyer policy requires human approval for counteroffers."
            )

        # Rule 2: Any policy violation requires human intervention.
        if policy_violations:
            approval_reasons.extend(
                f"Policy violation: {violation}"
                for violation in policy_violations
            )

        # Rule 3: Reaching the minimum acceptable price requires approval.
        if (
            counter_offer.proposed_price is not None
            and policy.minimum_acceptable_price is not None
            and counter_offer.proposed_price
            <= policy.minimum_acceptable_price
        ):
            approval_reasons.append(
                "Counteroffer reaches or approaches the minimum "
                "acceptable price boundary."
            )

        # Rule 4: Reaching the maximum discount requires approval.
        if (
            counter_offer.proposed_price is not None
            and context.current_price is not None
            and context.current_price > Decimal("0")
            and policy.maximum_discount_percent is not None
        ):
            discount = (
                (context.current_price - counter_offer.proposed_price)
                / context.current_price
            ) * Decimal("100")

            if discount >= policy.maximum_discount_percent:
                approval_reasons.append(
                    "Counteroffer reaches or exceeds the maximum "
                    "authorized discount."
                )

        # Rule 5: Reaching quantity boundaries requires approval.
        if counter_offer.proposed_quantity is not None:
            if (
                policy.minimum_quantity is not None
                and counter_offer.proposed_quantity
                <= policy.minimum_quantity
            ):
                approval_reasons.append(
                    "Counteroffer reaches the minimum quantity boundary."
                )

            if (
                policy.maximum_quantity is not None
                and counter_offer.proposed_quantity
                >= policy.maximum_quantity
            ):
                approval_reasons.append(
                    "Counteroffer reaches the maximum quantity boundary."
                )

        # Rule 6: Reaching the maximum delivery limit requires approval.
        if (
            counter_offer.proposed_delivery_days is not None
            and policy.maximum_delivery_days is not None
            and counter_offer.proposed_delivery_days
            >= policy.maximum_delivery_days
        ):
            approval_reasons.append(
                "Counteroffer reaches or exceeds the maximum "
                "delivery-time boundary."
            )

        # Rule 7: Changed payment terms require approval.
        if counter_offer.proposed_payment_terms is not None:
            current_terms = (context.payment_terms or "").strip().casefold()
            proposed_terms = (
                counter_offer.proposed_payment_terms.strip().casefold()
            )

            if proposed_terms != current_terms:
                approval_reasons.append(
                    "Payment terms have been changed."
                )

        # Rule 8: Changed warranty terms require approval.
        if counter_offer.proposed_warranty is not None:
            current_warranty = (context.warranty or "").strip().casefold()
            proposed_warranty = (
                counter_offer.proposed_warranty.strip().casefold()
            )

            if proposed_warranty != current_warranty:
                approval_reasons.append(
                    "Warranty terms have been changed."
                )

        # Approval is required whenever at least one reason exists.
        requires_approval = len(approval_reasons) > 0

        return requires_approval, approval_reasons
