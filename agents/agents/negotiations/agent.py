
from agents.negotiations.negotiator import Negotiator
from agents.negotiations.offer_calculator import OfferCalculator
from agents.negotiations.approval_checker import ApprovalChecker

from schemas.negotiation import (
    NegotiationContext,
    NegotiationPolicy,
    NegotiationResult,
    NegotiationStatus,
    NegotiationAction,
)
from schemas.evaluation import SupplierEvaluation


class NegotiationAgent:
    """
    Kraya's Supplier Negotiation Agent.

    Generates counteroffers, validates commercial limits,
    and determines whether human approval is required.

    Never sends messages or commits commercial terms.
    """

    def __init__(
        self,
        negotiator=None,
        offer_calculator=None,
        approval_checker=None,
    ):
        self.negotiator = negotiator or Negotiator()
        self.offer_calculator = offer_calculator or OfferCalculator()
        self.approval_checker = approval_checker or ApprovalChecker()

    def process_negotiation(
        self,
        context: NegotiationContext,
        policy: NegotiationPolicy,
        supplier_evaluation: SupplierEvaluation | None = None,
    ) -> NegotiationResult:

        # The integrated workflow passes Agent 8's deterministic evaluation.
        # Keep this guard here as well as in orchestration so a direct call
        # cannot negotiate for a supplier explicitly marked ineligible.
        if supplier_evaluation is not None and not supplier_evaluation.eligible:
            return NegotiationResult(
                supplier_name=context.supplier_name,
                status=NegotiationStatus.REJECTED,
                recommended_action=NegotiationAction.NO_ACTION,
                requires_human_approval=True,
                escalation_reason=(
                    "Supplier failed mandatory evaluation constraints; "
                    "negotiation is not permitted."
                ),
            )

        # Step 1: Check whether sufficient information is available.
        if (
            context.current_price is None
            or policy.minimum_acceptable_price is None
        ):
            return NegotiationResult(
                supplier_name=context.supplier_name,
                status=NegotiationStatus.INSUFFICIENT_INFORMATION,
                recommended_action=NegotiationAction.REQUEST_CLARIFICATION,
                requires_human_approval=True,
                escalation_reason=(
                    "Current supplier price or minimum acceptable "
                    "price is missing."
                ),
            )

        # Step 2: Generate a proposed counteroffer.
        counter_offer = self.negotiator.generate_counteroffer(
            context=context,
            policy=policy,
        )

        # Step 3: Validate the proposed commercial terms.
        violations = self.offer_calculator.validate_offer(
            context=context,
            counter_offer=counter_offer,
            policy=policy,
        )

        # Step 4: Never treat a policy-violating offer as ready.
        if violations:
            return NegotiationResult(
                supplier_name=context.supplier_name,
                status=NegotiationStatus.LIMIT_REACHED,
                recommended_action=NegotiationAction.ESCALATE_TO_HUMAN,
                counter_offer=counter_offer,
                policy_violations=violations,
                approval_reasons=[
                    "The proposed offer violates buyer-approved limits."
                ],
                requires_human_approval=True,
                escalation_reason=(
                    "The proposed counteroffer must be reviewed. "
                    "It must not be sent as drafted."
                ),
            )

        # Step 5: Check whether human approval is required.
        requires_approval, approval_reasons = (
            self.approval_checker.check_approval_required(
                context=context,
                counter_offer=counter_offer,
                policy=policy,
                policy_violations=violations,
            )
        )

        # Step 6: Return the final negotiation result.
        return NegotiationResult(
            supplier_name=context.supplier_name,
            status=(
                NegotiationStatus.APPROVAL_REQUIRED
                if requires_approval
                else NegotiationStatus.READY
            ),
            recommended_action=NegotiationAction.COUNTEROFFER,
            counter_offer=counter_offer,
            policy_violations=violations,
            approval_reasons=approval_reasons,
            requires_human_approval=requires_approval,
        )
