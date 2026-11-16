
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SupplierIntent(str, Enum):
    INTERESTED = "interested"
    QUOTATION_SUBMITTED = "quotation_submitted"
    NEEDS_CLARIFICATION = "needs_clarification"
    NEGOTIATING = "negotiating"
    DECLINED = "declined"
    UNRELATED = "unrelated"
    UNCLEAR = "unclear"


class RecommendedAction(str, Enum):
    REQUEST_INFORMATION = "request_information"
    REVIEW_QUOTATION = "review_quotation"
    NEGOTIATE = "negotiate"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    NO_ACTION = "no_action"


class SupplierIntentAnalysis(BaseModel):
    """Structured analysis of a supplier's email or reply."""

    intent: SupplierIntent

    intent_summary: str

    mentioned_details: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(default_factory=list)

    supplier_questions: list[str] = Field(default_factory=list)

    recommended_action: RecommendedAction

    clarification_questions: list[str] = Field(default_factory=list)

    draft_reply: Optional[str] = None

    requires_human_review: bool = False
