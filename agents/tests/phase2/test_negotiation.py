
from decimal import Decimal
from agents.negotiations.offer_calculator import OfferCalculator
import pytest
from pydantic import ValidationError

from schemas.negotiation import (
    NegotiationPolicy,
    NegotiationContext,
    NegotiationStatus,
    NegotiationAction,
    CounterOffer,
    NegotiationResult,
)


def test_valid_negotiation_policy():
    policy = NegotiationPolicy(
        target_price=Decimal("80000"),
        minimum_acceptable_price=Decimal("75000"),
        maximum_discount_percent=10,
        minimum_quantity=5,
        maximum_quantity=20,
        maximum_delivery_days=15,
    )

    assert policy.target_price == Decimal("80000")


def test_invalid_price_policy():
    with pytest.raises(ValidationError):
        NegotiationPolicy(
            target_price=Decimal("70000"),
            minimum_acceptable_price=Decimal("75000"),
        )


def test_invalid_quantity_policy():
    with pytest.raises(ValidationError):
        NegotiationPolicy(
            minimum_quantity=20,
            maximum_quantity=10,
        )


def test_negotiation_context():
    context = NegotiationContext(
        supplier_name="ABC Technologies",
        current_price=Decimal("890000"),
        current_quantity=10,
        delivery_days=15,
        delivery_unit="calendar_days",
    )

    assert context.supplier_name == "ABC Technologies"
    assert context.current_quantity == 10


def test_counteroffer():
    offer = CounterOffer(
        proposed_price=Decimal("850000"),
        negotiation_reason="Requesting a better bulk purchase price.",
    )

    assert offer.proposed_price == Decimal("850000")


def test_negotiation_result():
    result = NegotiationResult(
        supplier_name="ABC Technologies",
        status=NegotiationStatus.READY,
        recommended_action=NegotiationAction.COUNTEROFFER,
        requires_human_approval=True,
    )

    assert result.status == NegotiationStatus.READY
    assert result.requires_human_approval is True


def test_calculate_discount():
    calculator = OfferCalculator()

    discount = calculator.calculate_discount(
        Decimal("100000"),
        Decimal("90000"),
    )

    assert discount == Decimal("10.00")


def test_price_within_policy():
    calculator = OfferCalculator()

    policy = NegotiationPolicy(
        minimum_acceptable_price=Decimal("75000"),
        maximum_discount_percent=10,
    )

    violations = calculator.validate_price(
        current_price=Decimal("100000"),
        proposed_price=Decimal("90000"),
        policy=policy,
    )

    assert violations == []


def test_price_below_minimum():
    calculator = OfferCalculator()

    policy = NegotiationPolicy(
        minimum_acceptable_price=Decimal("75000"),
    )

    violations = calculator.validate_price(
        current_price=Decimal("100000"),
        proposed_price=Decimal("70000"),
        policy=policy,
    )

    assert len(violations) > 0


def test_discount_exceeds_limit():
    calculator = OfferCalculator()

    policy = NegotiationPolicy(
        minimum_acceptable_price=Decimal("70000"),
        maximum_discount_percent=10,
    )

    violations = calculator.validate_price(
        current_price=Decimal("100000"),
        proposed_price=Decimal("85000"),
        policy=policy,
    )

    assert any("discount" in v.lower() for v in violations)


def test_quantity_exceeds_limit():
    calculator = OfferCalculator()

    policy = NegotiationPolicy(
        minimum_quantity=5,
        maximum_quantity=20,
    )

    violations = calculator.validate_quantity(
        proposed_quantity=25,
        policy=policy,
    )

    assert len(violations) > 0


def test_delivery_exceeds_limit():
    calculator = OfferCalculator()

    policy = NegotiationPolicy(
        maximum_delivery_days=15,
        allowed_delivery_unit="calendar_days",
    )

    violations = calculator.validate_delivery(
        proposed_delivery_days=20,
        proposed_delivery_unit="calendar_days",
        policy=policy,
    )

    assert len(violations) > 0


from unittest.mock import Mock

from agents.negotiations.agent import NegotiationAgent


def test_negotiation_agent_requires_approval():
    mock_negotiator = Mock()
    mock_calculator = Mock()
    mock_approval_checker = Mock()

    mock_negotiator.generate_counteroffer.return_value = CounterOffer(
        proposed_price=Decimal("85000"),
        negotiation_reason="Requesting a bulk discount.",
        message_draft="Could you offer a better price?",
    )

    mock_calculator.validate_offer.return_value = []
    mock_approval_checker.check_approval_required.return_value = (
        True,
        ["Buyer policy requires human approval."],
    )

    agent = NegotiationAgent(
        negotiator=mock_negotiator,
        offer_calculator=mock_calculator,
        approval_checker=mock_approval_checker,
    )

    context = NegotiationContext(
        supplier_name="ABC Technologies",
        current_price=Decimal("100000"),
    )

    policy = NegotiationPolicy(
        minimum_acceptable_price=Decimal("75000"),
        requires_human_approval=True,
    )

    result = agent.process_negotiation(context, policy)

    assert result.status == NegotiationStatus.APPROVAL_REQUIRED
    assert result.requires_human_approval is True
    assert result.counter_offer.proposed_price == Decimal("85000")


def test_negotiation_agent_blocks_policy_violation():
    mock_negotiator = Mock()
    mock_calculator = Mock()

    mock_negotiator.generate_counteroffer.return_value = CounterOffer(
        proposed_price=Decimal("70000"),
        negotiation_reason="Requesting a discount.",
    )

    mock_calculator.validate_offer.return_value = [
        "Proposed price is below the minimum acceptable price."
    ]

    agent = NegotiationAgent(
        negotiator=mock_negotiator,
        offer_calculator=mock_calculator,
        approval_checker=Mock(),
    )

    context = NegotiationContext(
        supplier_name="ABC Technologies",
        current_price=Decimal("100000"),
    )

    policy = NegotiationPolicy(
        minimum_acceptable_price=Decimal("75000"),
    )

    result = agent.process_negotiation(context, policy)

    assert result.status == NegotiationStatus.LIMIT_REACHED
    assert result.requires_human_approval is True
    assert len(result.policy_violations) == 1
    mock_approval_checker = agent.approval_checker
    mock_approval_checker.check_approval_required.assert_not_called()


def test_negotiation_agent_handles_missing_information():
    agent = NegotiationAgent(
        negotiator=Mock(),
        offer_calculator=Mock(),
        approval_checker=Mock(),
    )

    context = NegotiationContext(
        supplier_name="ABC Technologies",
    )

    policy = NegotiationPolicy(
        minimum_acceptable_price=None,
    )

    result = agent.process_negotiation(context, policy)

    assert result.status == NegotiationStatus.INSUFFICIENT_INFORMATION
    assert result.requires_human_approval is True

