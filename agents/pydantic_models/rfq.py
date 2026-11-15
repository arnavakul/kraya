
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pydantic_models.requirement import Requirement
from pydantic_models.supplier_candidate import SupplierCandidate


class RFQDraft(BaseModel):
    """
    Represents one supplier-specific RFQ draft.
    """

    rfq_id: UUID = Field(default_factory=uuid4)

    requirement: Requirement
    supplier: SupplierCandidate

    email_subject: str
    email_body: str

    status: Literal[
        "draft",
        "pending_approval",
        "approved",
        "rejected"
    ] = "draft"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class RFQDraftingResult(BaseModel):
    """
    Result returned by the RFQ Drafting Agent.
    """

    status: Literal[
        "completed",
        "partial",
        "failed"
    ]

    total_suppliers: int = 0
    successful_drafts: int = 0
    failed_drafts: int = 0

    rfq_drafts: list[RFQDraft] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )
