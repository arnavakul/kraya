
from typing import Literal

from pydantic import BaseModel, Field


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

    total_fetched: int = 0
    total_processed: int = 0
    total_skipped: int = 0
    total_failed: int = 0
