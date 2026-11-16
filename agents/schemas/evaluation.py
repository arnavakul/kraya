
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas.ml_evaluation import ShapBreakdown


class ConstraintStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class MLEvaluationStatus(str, Enum):
    NOT_RUN = "not_run"
    COMPLETED = "completed"
    SKIPPED_MISSING_FEATURES = "skipped_missing_features"
    SKIPPED_API_UNAVAILABLE = "skipped_api_unavailable"
    FAILED = "failed"


class SupplierEvaluation(BaseModel):
    supplier_name: str

    mandatory_constraints: dict[str, ConstraintStatus]

    eligible: bool

    criterion_scores: dict[str, float] = Field(default_factory=dict)

    criterion_availability: dict[str, bool] = Field(default_factory=dict)

    weighted_score: float = Field(ge=0, le=100)

    ranking: Optional[int] = None

    strengths: list[str] = Field(default_factory=list)

    weaknesses: list[str] = Field(default_factory=list)

    trade_offs: list[str] = Field(default_factory=list)

    evaluation_status: str = "pending_verification"

    # Additional ML evaluation information.
    ml_status: MLEvaluationStatus = MLEvaluationStatus.NOT_RUN

    ml_score: Optional[float] = Field(default=None, ge=0, le=100)

    ml_baseline_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    ml_shap_breakdown: Optional[ShapBreakdown] = None

    ml_missing_features: list[str] = Field(default_factory=list)

    ml_reasons: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    evaluations: list[SupplierEvaluation]

    recommended_supplier: Optional[str] = None

    recommendation_summary: str = ""

    recommendation_reasoning: list[str] = Field(default_factory=list)
