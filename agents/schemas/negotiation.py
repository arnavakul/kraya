
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class NegotiationStatus(str, Enum):
    READY = "ready"
    LIMIT_REACHED = "limit_reached"
    APPROVAL_REQUIRED = "approval_required"
    REJECTED = "rejected"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class NegotiationAction(str, Enum):
    COUNTEROFFER = "counteroffer"
    ACCEPT_OFFER = "accept_offer"
    REQUEST_CLARIFICATION = "request_clarification"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    NO_ACTION = "no_action"


class NegotiationPolicy(BaseModel):
    """
    Buyer-approved limits within which the agent can negotiate.
    """

    target_price: Optional[Decimal] = None
    minimum_acceptable_price: Optional[Decimal] = None
    maximum_discount_percent: Optional[Decimal] = Field(
        default=None, ge=0, le=100
    )

    minimum_quantity: Optional[int] = Field(default=None, ge=1)
    maximum_quantity: Optional[int] = Field(default=None, ge=1)

    maximum_delivery_days: Optional[int] = Field(default=None, ge=1)
    allowed_delivery_unit: str = "calendar_days"

    requires_human_approval: bool = True

    @model_validator(mode="after")
    def validate_policy(self):
        if (
            self.target_price is not None
            and self.minimum_acceptable_price is not None
            and self.target_price < self.minimum_acceptable_price
        ):
            raise ValueError(
                "Target price cannot be below minimum acceptable price."
            )

        if (
            self.minimum_quantity is not None
            and self.maximum_quantity is not None
            and self.minimum_quantity > self.maximum_quantity
        ):
            raise ValueError(
                "Minimum quantity cannot exceed maximum quantity."
            )

        return self


class NegotiationContext(BaseModel):
    """
    Information required to make a negotiation decision.
    """

    supplier_name: str
    current_price: Optional[Decimal] = None
    current_quantity: Optional[int] = None

    delivery_days: Optional[int] = None
    delivery_unit: Optional[str] = None

    payment_terms: Optional[str] = None
    warranty: Optional[str] = None

    conversation_history: list[str] = Field(default_factory=list)
    buyer_instructions: Optional[str] = None


class CounterOffer(BaseModel):
    """
    Proposed changes to the supplier's commercial terms.
    """

    proposed_price: Optional[Decimal] = None
    proposed_quantity: Optional[int] = None
    proposed_delivery_days: Optional[int] = None
    proposed_delivery_unit: Optional[str] = None

    proposed_payment_terms: Optional[str] = None
    proposed_warranty: Optional[str] = None

    negotiation_reason: str
    message_draft: Optional[str] = None


class NegotiationResult(BaseModel):
    """
    Final structured output from the Negotiation Agent.
    """

    supplier_name: str
    status: NegotiationStatus
    recommended_action: NegotiationAction

    counter_offer: Optional[CounterOffer] = None

    policy_violations: list[str] = Field(default_factory=list)
    approval_reasons: list[str] = Field(default_factory=list)

    requires_human_approval: bool = True
    escalation_reason: Optional[str] = None
