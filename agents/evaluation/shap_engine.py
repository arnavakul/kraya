import joblib
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List
from agents.pydantic_models.evaluation_schemas import (
    FeatureVector,
    FeatureImpact,
    ShapBreakdown,
    EvaluationResponse
)

# Feature display label mapping for UI rendering
FEATURE_LABELS = {
    "price_variance_pct": "Price vs. Budget Target",
    "tco_markup_pct": "Additional Landed Costs (TCO)",
    "lead_time_days_delta": "Lead Time Alignment",
    "historical_delay_avg_days": "Historical Delivery Delay",
    "historical_defect_rate": "Historical Order Defect Rate",
    "payment_terms_penalty": "Payment Terms Compliance",
    "warranty_months": "Warranty Duration",
    "category_experience_years": "Category Experience",
    "extraction_completeness_pct": "Quote Extraction Completeness",
    "anomaly_lowball_flag": "Low-Ball Anomaly Risk"
}

class ShapEvaluationEngine:
    def __init__(self, model_path: str = "agents/models/evaluation_xgb_v1.bin"):
        # Load the trained XGBoost model
        self.model = joblib.load(model_path)
        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)

    def _prepare_dataframe(self, feature_vector: FeatureVector) -> pd.DataFrame:
        data = feature_vector.model_dump()
        
        # Apply default neutral imputations if historical metrics are missing (Cold-Start)
        if data["historical_delay_avg_days"] is None:
            data["historical_delay_avg_days"] = 0.0
        if data["historical_defect_rate"] is None:
            data["historical_defect_rate"] = 0.0
            
        return pd.DataFrame([data])

    def evaluate_and_explain(
        self, 
        supplier_id: str, 
        quote_id: str, 
        feature_vector: FeatureVector
    ) -> EvaluationResponse:
        df_input = self._prepare_dataframe(feature_vector)
        
        # 1. Run XGBoost Prediction
        raw_score = float(self.model.predict(df_input)[0])
        final_score = round(float(np.clip(raw_score, 0.0, 100.0)), 2)
        
        # 2. Calculate SHAP Values
        shap_values = self.explainer(df_input)
        base_value = round(float(shap_values.base_values[0]), 2)
        feature_shaps = shap_values.values[0]
        
        # 3. Process and Rank Feature Drivers
        positive_drivers: List[FeatureImpact] = []
        negative_drivers: List[FeatureImpact] = []
        
        for col_name, shap_val in zip(df_input.columns, feature_shaps):
            val_str = str(df_input[col_name].iloc[0])
            score_delta = round(float(shap_val), 2)
            
            # Skip negligible feature impacts
            if abs(score_delta) < 0.1:
                continue
                
            impact = FeatureImpact(
                feature_name=col_name,
                display_label=FEATURE_LABELS.get(col_name, col_name),
                feature_value=val_str,
                shap_value=round(float(shap_val), 4),
                score_delta=score_delta
            )
            
            if score_delta > 0:
                positive_drivers.append(impact)
            else:
                negative_drivers.append(impact)
                
        # Sort drivers by absolute impact magnitude
        positive_drivers.sort(key=lambda x: x.score_delta, reverse=True)
        negative_drivers.sort(key=lambda x: x.score_delta)
        
        return EvaluationResponse(
            supplier_id=supplier_id,
            quote_id=quote_id,
            final_score=final_score,
            baseline_score=base_value,
            shap_breakdown=ShapBreakdown(
                base_value=base_value,
                top_positive_drivers=positive_drivers,
                top_negative_drivers=negative_drivers
            )
        )