from pydantic import BaseModel, Field
from typing import List, Optional

class FeatureVector(BaseModel):
    # Commercial & Price Alignment
    price_variance_pct: float = Field(..., description="Percentage difference from category target budget (e.g., -0.05 for 5% under)")
    tco_markup_pct: float = Field(0.0, description="Freight, taxes, and additional landed costs percentage")
    
    # Operational Reliability
    lead_time_days_delta: float = Field(..., description="Days difference between promised delivery and required deadline")
    historical_delay_avg_days: Optional[float] = Field(None, description="Average historical delivery delay (None for new suppliers)")
    historical_defect_rate: Optional[float] = Field(None, description="Historical order defect percentage (None for new suppliers)")
    
    # Commercial Terms & Flexibility
    payment_terms_penalty: float = Field(0.0, description="Penalty points for policy deviation (e.g., 0.0 for Net 60, 1.0 for Net 30)")
    warranty_months: float = Field(12.0, description="Warranty duration in months")
    
    # Supplier Profile & Anomaly Flags
    category_experience_years: float = Field(1.0, description="Years of experience in this specific procurement category")
    extraction_completeness_pct: float = Field(1.0, description="Percentage of required fields successfully extracted from PDF quote")
    anomaly_lowball_flag: float = Field(0.0, description="Binary flag indicating an abnormally low quote price (0.0 or 1.0)")

class FeatureImpact(BaseModel):
    feature_name: str
    display_label: str
    feature_value: str
    shap_value: float
    score_delta: float

class ShapBreakdown(BaseModel):
    base_value: float
    top_positive_drivers: List[FeatureImpact]
    top_negative_drivers: List[FeatureImpact]

class EvaluationResponse(BaseModel):
    supplier_id: str
    quote_id: str
    final_score: float
    baseline_score: float
    shap_breakdown: ShapBreakdown