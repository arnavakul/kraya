
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from agents.evaluation.predictor import XGBoostPredictor
from agents.evaluation.feature_pipeline import FeatureVectorSchema


@pytest.fixture
def sample_features():
    return FeatureVectorSchema(
        price_variance_pct=-0.05,
        tco_markup_pct=0.03,
        lead_time_days_delta=-2.0,
        historical_delay_avg_days=1.2,
        historical_defect_rate=0.01,
        payment_terms_penalty=0.0,
        warranty_months=24.0,
        category_experience_years=5.0,
        extraction_completeness_pct=0.98,
        anomaly_lowball_flag=0.0,
    )


@pytest.fixture
def fake_model_file(tmp_path):
    model_file = tmp_path / "fake_model.bin"
    model_file.touch()
    return str(model_file)


@patch("agents.evaluation.predictor.joblib.load")
def test_predict_returns_score(
    mock_load, sample_features, fake_model_file
):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([82.567])
    mock_load.return_value = mock_model

    predictor = XGBoostPredictor(model_path=fake_model_file)

    score = predictor.predict(sample_features)

    assert score == 82.57


@patch("agents.evaluation.predictor.joblib.load")
def test_predict_clips_score(
    mock_load, sample_features, fake_model_file
):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([110.0])
    mock_load.return_value = mock_model

    predictor = XGBoostPredictor(model_path=fake_model_file)

    assert predictor.predict(sample_features) == 100.0


@patch("agents.evaluation.predictor.joblib.load")
def test_predict_rejects_invalid_prediction(
    mock_load, sample_features, fake_model_file
):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([np.nan])
    mock_load.return_value = mock_model

    predictor = XGBoostPredictor(model_path=fake_model_file)

    with pytest.raises(ValueError, match="invalid prediction"):
        predictor.predict(sample_features)


@patch("agents.evaluation.predictor.joblib.load")
def test_predict_rejects_multiple_predictions(
    mock_load, sample_features, fake_model_file
):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([80.0, 90.0])
    mock_load.return_value = mock_model

    predictor = XGBoostPredictor(model_path=fake_model_file)

    with pytest.raises(ValueError, match="exactly one prediction"):
        predictor.predict(sample_features)
