
import pytest

from agents.evaluation.shap_engine import ShapEvaluationEngine
from schemas.ml_evaluation import FeatureVector


@pytest.fixture
def sample_features():
    return FeatureVector(
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
def shap_engine():
    return ShapEvaluationEngine()


def test_shap_engine_generates_evaluation(
    shap_engine, sample_features
):
    result = shap_engine.evaluate_and_explain(
        supplier_id="SUP-001",
        quote_id="QUOTE-001",
        feature_vector=sample_features,
    )

    assert result.supplier_id == "SUP-001"
    assert result.quote_id == "QUOTE-001"
    assert 0 <= result.final_score <= 100
    assert isinstance(result.baseline_score, float)


def test_shap_engine_generates_feature_explanations(
    shap_engine, sample_features
):
    result = shap_engine.evaluate_and_explain(
        supplier_id="SUP-001",
        quote_id="QUOTE-001",
        feature_vector=sample_features,
    )

    positive = result.shap_breakdown.top_positive_drivers
    negative = result.shap_breakdown.top_negative_drivers

    assert len(positive) + len(negative) > 0

    for driver in positive:
        assert driver.score_delta > 0

    for driver in negative:
        assert driver.score_delta < 0


def test_shap_engine_uses_expected_features(
    shap_engine, sample_features
):
    result = shap_engine.evaluate_and_explain(
        supplier_id="SUP-001",
        quote_id="QUOTE-001",
        feature_vector=sample_features,
    )

    positive = result.shap_breakdown.top_positive_drivers
    negative = result.shap_breakdown.top_negative_drivers

    all_drivers = positive + negative

    expected_features = {
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
    }

    for driver in all_drivers:
        assert driver.feature_name in expected_features
