from pathlib import Path
from typing import Optional
import joblib
import pandas as pd
import xgboost as xgb

# Default path to your saved trained model artifact (adjust filename/extension to match yours)
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "xgboost_supplier_scorer.json"

_model_instance: Optional[xgb.XGBRegressor] = None


def load_model(model_path: str | Path = DEFAULT_MODEL_PATH):
    """
    Loads the trained XGBoost model from disk once and caches it in memory.
    Supports both native XGBoost (.json / .ubj) and scikit-learn joblib (.joblib / .pkl) formats.
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Trained XGBoost model not found at: {path}")

    if path.suffix in {".json", ".ubj"}:
        model = xgb.XGBRegressor()
        model.load_model(str(path))
    else:
        model = joblib.load(path)

    _model_instance = model
    return _model_instance


def get_model():
    """Returns the cached XGBoost model instance (used by both predictor and shap_engine)."""
    return load_model()


def classify_risk_tier(score: float) -> str:
    """Maps the 0-100 composite score to an actionable procurement risk band."""
    if score >= 75.0:
        return "LOW"
    elif score >= 50.0:
        return "MEDIUM"
    return "HIGH"


def predict_score(features_df: pd.DataFrame) -> dict:
    """
    Runs XGBoost inference on a single-row, 10-column ordered DataFrame
    produced by feature_pipeline.vectorize_for_inference().
    """
    model = get_model()
    raw_pred = float(model.predict(features_df)[0])

    # Clamp score safely between 0 and 100
    composite_score = round(max(0.0, min(100.0, raw_pred)), 2)

    return {
        "score": composite_score,
        "risk_tier": classify_risk_tier(composite_score),
    }