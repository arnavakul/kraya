
from typing import Any, Literal

from pydantic import BaseModel, Field
from schemas.suppliers_intent import SupplierIntentAnalysis


EmailCategory = Literal[
    "quotation",
    "question",
    "rejection",
    "follow_up",
    "spam",
    "out_of_office",
    "suspicious"
]


RoutingAction = Literal[
    "quotation_processing",
    "clarification_workflow",
    "supplier_response_update",
    "follow_up_workflow",
    "await_supplier_response",
    "quarantine",
    "security_review",
    "manual_review"
]


class InboxTriageResult(BaseModel):

    email_id: str

    category: EmailCategory

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    summary: str

    requires_human_review: bool = False

    security_flags: list[str] = Field(
        default_factory=list
    )

    routing_action: RoutingAction



class InboxProcessingFailure(BaseModel):
    email_id: str
    stage: Literal[
        "claim",
        "screening",
        "classification",
        "routing",
        "persistence"
    ]
    error: str


class QuotationProcessingResult(BaseModel):
    email_id: str
    thread_id: str | None = None
    in_reply_to: str | None = None
    sender_email: str
    sender_name: str | None = None
    status: Literal["completed", "needs_review", "failed"]
    quotation: dict[str, Any] | None = None
    financial_validation: dict[str, Any] | None = None
    error: str | None = None
    requires_human_review: bool = False


class SupplierIntentProcessingResult(BaseModel):
    email_id: str
    thread_id: str | None = None
    in_reply_to: str | None = None
    sender_email: str
    sender_name: str | None = None
    status: Literal["completed", "failed"]
    analysis: SupplierIntentAnalysis | None = None
    error: str | None = None
    requires_human_review: bool = False


class InboxTriageRunResult(BaseModel):
    processed_emails: list[InboxTriageResult] = Field(
        default_factory=list
    )

    skipped_email_ids: list[str] = Field(
        default_factory=list
    )

    failed_emails: list[InboxProcessingFailure] = Field(
        default_factory=list
    )

    quotation_processing_results: list[QuotationProcessingResult] = Field(
        default_factory=list
    )

    supplier_intent_results: list[SupplierIntentProcessingResult] = Field(
        default_factory=list
    )

    total_fetched: int = 0
    total_processed: int = 0
    total_skipped: int = 0
    total_failed: int = 0
