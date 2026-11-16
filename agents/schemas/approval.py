
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalAction(str, Enum):
    SUPPLIER_SELECTION = "supplier_selection"
    PRICE_COMMITMENT = "price_commitment"
    POLICY_EXCEPTION = "policy_exception"
    SENSITIVE_ACTION = "sensitive_action"


class ApprovalRequest(BaseModel):
    """Represents a procurement action awaiting human approval."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    requester_user_id: str

    action: ApprovalAction
    entity_type: str
    entity_id: str

    reason: str
    evidence: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    """Records a human approval or rejection."""

    model_config = ConfigDict(extra="forbid")

    approval_id: str
    reviewer_user_id: str

    status: ApprovalStatus
    comments: Optional[str] = None



class ApprovalRecord(BaseModel):
    """Represents the approval workflow record."""

    model_config = ConfigDict(extra="forbid")

    id: str
    organization_id: str
    requester_user_id: str

    action: ApprovalAction
    entity_type: str
    entity_id: str

    reason: str
    evidence: list[str] = Field(default_factory=list)

    status: ApprovalStatus = ApprovalStatus.PENDING

    reviewer_user_id: Optional[str] = None
    reviewer_comments: Optional[str] = None

    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None

