from typing import Dict, Any, List
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Exact feature order expected by the trained XGBoost model and TreeSHAP explainer
FEATURE_COLUMNS: List[str] = [
    "price_variance_pct",
    "tco_markup_pct",
    "lead_time_days_delta",
    "historical_delay_avg_days",
    "historical_defect_rate",
    "payment_terms_penalty",
    "warranty_months",
    "category_experience_years",
    "extraction_completeness_pct",
    "anomaly_lowball_flag",
]


class FeatureVectorSchema(BaseModel):
    """Pydantic schema validating the 10-feature vector sent by Spring Boot."""
    price_variance_pct: float = Field(..., description="Quote price variance vs market benchmark")
    tco_markup_pct: float = Field(..., description="Total cost of ownership hidden markup ratio")
    lead_time_days_delta: float = Field(..., description="Delivery lead time difference in days")
    historical_delay_avg_days: float = Field(..., ge=0.0, description="Vendor past average delay in days")
    historical_defect_rate: float = Field(..., ge=0.0, le=1.0, description="Vendor past defect ratio")
    payment_terms_penalty: float = Field(..., ge=0.0, description="Penalty score for non-standard payment terms")
    warranty_months: float = Field(..., ge=0.0, description="Offered warranty duration in months")
    category_experience_years: float = Field(..., ge=0.0, description="Vendor years of experience in category")
    extraction_completeness_pct: float = Field(..., ge=0.0, le=1.0, description="Quote document completeness score")
    anomaly_lowball_flag: float = Field(..., description="1.0 if suspiciously lowball price, else 0.0")


def build_features_from_raw(
    quoted_price: float,
    market_benchmark_price: float,
    shipping_and_hidden_costs: float,
    quoted_lead_time_days: float,
    target_lead_time_days: float,
    historical_delay_avg_days: float = 0.0,
    historical_defect_rate: float = 0.0,
    payment_terms_days: int = 30,
    warranty_months: float = 12.0,
    category_experience_years: float = 1.0,
    extracted_fields_count: int = 10,
    total_required_fields: int = 10,
) -> FeatureVectorSchema:
    """
    Computes the 10 standardized features from raw quote, market, and supplier history inputs.
    """
    # 1. Price variance percentage relative to benchmark
    price_variance_pct = (
        (quoted_price - market_benchmark_price) / market_benchmark_price
        if market_benchmark_price > 0
        else 0.0
    )

    # 2. TCO markup percentage
    tco_markup_pct = (
        shipping_and_hidden_costs / quoted_price
        if quoted_price > 0
        else 0.0
    )

    # 3. Lead time delta (negative = faster than target)
    lead_time_days_delta = quoted_lead_time_days - target_lead_time_days

    # 4. Payment terms penalty (e.g., upfront/Net-15 incurs penalty vs standard Net-30/60)
    if payment_terms_days < 15:
        payment_terms_penalty = 0.15
    elif payment_terms_days < 30:
        payment_terms_penalty = 0.05
    else:
        payment_terms_penalty = 0.0

    # 5. Document extraction completeness
    extraction_completeness_pct = (
        min(extracted_fields_count / total_required_fields, 1.0)
        if total_required_fields > 0
        else 0.0
    )

    # 6. Low-ball anomaly detection flag (e.g., >25% below market benchmark)
    anomaly_lowball_flag = 1.0 if price_variance_pct < -0.25 else 0.0

    return FeatureVectorSchema(
        price_variance_pct=round(price_variance_pct, 4),
        tco_markup_pct=round(tco_markup_pct, 4),
        lead_time_days_delta=round(lead_time_days_delta, 2),
        historical_delay_avg_days=round(historical_delay_avg_days, 2),
        historical_defect_rate=round(historical_defect_rate, 4),
        payment_terms_penalty=round(payment_terms_penalty, 4),
        warranty_months=float(warranty_months),
        category_experience_years=float(category_experience_years),
        extraction_completeness_pct=round(extraction_completeness_pct, 4),
        anomaly_lowball_flag=anomaly_lowball_flag,
    )


def vectorize_for_inference(payload: Dict[str, Any] | FeatureVectorSchema) -> pd.DataFrame:
    """
    Converts a validated feature dictionary or schema into a single-row Pandas DataFrame
    with columns strictly ordered for XGBoost and TreeSHAP inference.
    """
    if isinstance(payload, FeatureVectorSchema):
        data = payload.model_dump()
    else:
        validated = FeatureVectorSchema(**payload)
        data = validated.model_dump()

    # Enforce strict column ordering matching training time
    ordered_row = {col: float(data[col]) for col in FEATURE_COLUMNS}
    return pd.DataFrame([ordered_row], columns=FEATURE_COLUMNS)