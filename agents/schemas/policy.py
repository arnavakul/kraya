
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class PolicyCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check_name: str
    status: CheckStatus
    reason: str


class PolicyEvaluationRequest(BaseModel):
    """Information required to evaluate a procurement action."""

    model_config = ConfigDict(extra="forbid")

    organization_id: str
    user_id: str
    action: str

    user_role: str
    user_status: str
    organization_status: str

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

    supplier_status: Optional[str] = None

    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    spending_limit: Optional[float] = Field(default=None, ge=0)
    spending_limit_currency: Optional[str] = None
    untrusted_message: Optional[str] = None


class PolicyEvaluationResult(BaseModel):
    """Final decision returned by the Policy Guardrails Agent."""

    model_config = ConfigDict(extra="forbid")

    decision: PolicyDecision
    risk_level: RiskLevel

    checks: list[PolicyCheckResult] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)

    requires_human_review: bool = False
