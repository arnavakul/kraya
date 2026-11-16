
from typing import Optional

from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """Input features expected by the ML evaluation API."""

    price_variance_pct: float

    tco_markup_pct: float = 0.0

    lead_time_days_delta: float

    historical_delay_avg_days: Optional[float] = None

    historical_defect_rate: Optional[float] = None

    payment_terms_penalty: float = 0.0

    warranty_months: float = 12.0

    category_experience_years: float = 1.0

    extraction_completeness_pct: float = 1.0

    anomaly_lowball_flag: float = 0.0


class FeatureImpact(BaseModel):
    """Contribution of one feature to the predicted score."""

    feature_name: str
    display_label: str
    feature_value: str
    shap_value: float
    score_delta: float


class ShapBreakdown(BaseModel):
    """Positive and negative SHAP contributions."""

    base_value: float

    top_positive_drivers: list[FeatureImpact]

    top_negative_drivers: list[FeatureImpact]


class EvaluationResponse(BaseModel):
    """Complete response returned by the ML evaluation API."""

    supplier_id: str
    quote_id: str

    final_score: float

    baseline_score: float

    shap_breakdown: ShapBreakdown
