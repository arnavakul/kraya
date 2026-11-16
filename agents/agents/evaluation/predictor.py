
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from agents.evaluation.feature_pipeline import (
    FeatureVectorSchema,
    vectorize_for_inference,
)


class XGBoostPredictor:
    """
    Loads the trained XGBoost model and predicts supplier evaluation scores.
    """

    def __init__(self, model_path: str | None = None):

        # Resolve model location relative to this file.
        if model_path is None:
            candidates = [
                Path(__file__).resolve().parents[2] / "models" / "evaluation_xgb_v1.bin",
                Path(__file__).resolve().parents[1] / "models" / "evaluation_xgb_v1.bin",
                Path("models/evaluation_xgb_v1.bin").resolve(),
            ]
            for candidate in candidates:
                if candidate.exists():
                    model_path = candidate
                    break
            if model_path is None:
                model_path = candidates[0]

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"XGBoost model not found: {self.model_path}"
            )

        # Load the previously trained model.
        self.model = joblib.load(self.model_path)

    def predict(
        self,
        features: FeatureVectorSchema | dict[str, Any],
    ) -> float:
        """
        Accepts validated features and returns a score between 0 and 100.
        """

        # Convert features into the exact DataFrame expected by XGBoost.
        dataframe = vectorize_for_inference(features)

        # Generate prediction.
        prediction = self.model.predict(dataframe)

        if len(prediction) != 1:
            raise ValueError(
                "Expected exactly one prediction for one supplier."
            )

        raw_score = float(prediction[0])

        if not np.isfinite(raw_score):
            raise ValueError(
                "XGBoost returned an invalid prediction."
            )

        # Keep evaluation score within the 0-100 range.
        final_score = float(
            np.clip(raw_score, 0.0, 100.0)
        )

        return round(final_score, 2)
