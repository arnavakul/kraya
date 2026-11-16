
from typing import List

import numpy as np
import shap

from schemas.ml_evaluation import (
    FeatureVector,
    FeatureImpact,
    ShapBreakdown,
    EvaluationResponse,
)

from agents.evaluation.feature_pipeline import (
    FeatureVectorSchema,
    vectorize_for_inference,
)

from agents.evaluation.predictor import XGBoostPredictor


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
    "anomaly_lowball_flag": "Low-Ball Anomaly Risk",
}


class ShapEvaluationEngine:
    """
    Evaluates supplier quotations using XGBoost and explains
    predictions using TreeSHAP.
    """

    def __init__(self, model_path: str | None = None):

        # Load the model once through our predictor.
        self.predictor = XGBoostPredictor(model_path=model_path)

        # Reuse the predictor's already-loaded model.
        self.model = self.predictor.model

        # Initialize TreeSHAP.
        self.explainer = shap.TreeExplainer(self.model)

    def _prepare_features(
        self,
        feature_vector: FeatureVector,
    ) -> FeatureVectorSchema:
        """
        Convert API input into the validated feature pipeline schema.

        Missing historical values are imputed to zero, matching
        the existing evaluation engine's behavior.
        """

        data = feature_vector.model_dump()

        if data["historical_delay_avg_days"] is None:
            data["historical_delay_avg_days"] = 0.0

        if data["historical_defect_rate"] is None:
            data["historical_defect_rate"] = 0.0

        return FeatureVectorSchema.model_validate(data)

    def evaluate_and_explain(
        self,
        supplier_id: str,
        quote_id: str,
        feature_vector: FeatureVector,
    ) -> EvaluationResponse:

        # Step 1: Validate and prepare features.
        validated_features = self._prepare_features(feature_vector)

        # Step 2: Create the correctly ordered DataFrame.
        df_input = vectorize_for_inference(validated_features)

        # Step 3: Generate prediction through our predictor.
        final_score = self.predictor.predict(validated_features)

        # Step 4: Calculate SHAP values using the same DataFrame.
        shap_values = self.explainer(df_input)

        base_value = round(
            float(np.asarray(shap_values.base_values).reshape(-1)[0]),
            2,
        )

        feature_shaps = np.asarray(shap_values.values).reshape(-1)

        if len(feature_shaps) != len(df_input.columns):
            raise ValueError(
                "SHAP feature count does not match input feature count."
            )

        # Step 5: Separate positive and negative contributions.
        positive_drivers: List[FeatureImpact] = []
        negative_drivers: List[FeatureImpact] = []

        for col_name, shap_val in zip(
            df_input.columns,
            feature_shaps,
        ):

            score_delta = round(float(shap_val), 2)

            # Ignore insignificant contributions.
            if abs(score_delta) < 0.1:
                continue

            feature_value = str(df_input[col_name].iloc[0])

            impact = FeatureImpact(
                feature_name=col_name,
                display_label=FEATURE_LABELS.get(
                    col_name, col_name
                ),
                feature_value=feature_value,
                shap_value=round(float(shap_val), 4),
                score_delta=score_delta,
            )

            if score_delta > 0:
                positive_drivers.append(impact)
            else:
                negative_drivers.append(impact)

        # Step 6: Sort contributions by impact.
        positive_drivers.sort(
            key=lambda x: x.score_delta,
            reverse=True,
        )

        negative_drivers.sort(
            key=lambda x: x.score_delta,
        )

        # Step 7: Return structured evaluation response.
        return EvaluationResponse(
            supplier_id=supplier_id,
            quote_id=quote_id,
            final_score=final_score,
            baseline_score=base_value,
            shap_breakdown=ShapBreakdown(
                base_value=base_value,
                top_positive_drivers=positive_drivers,
                top_negative_drivers=negative_drivers,
            ),
        )
