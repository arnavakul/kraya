import pytest
from evaluation.shap_engine import ShapEvaluationEngine
from pydantic_models.evaluation_schemas import FeatureVector


@pytest.fixture
def shap_engine():
    """Fixture to initialize the SHAP evaluation engine."""
    return ShapEvaluationEngine(model_path="models/evaluation_xgb_v1.bin")


def test_score_and_explain_standard_supplier(shap_engine):
    """Test standard supplier evaluation with complete historical data."""
    features = FeatureVector(
        price_variance_pct=-0.05,
        tco_markup_pct=0.02,
        lead_time_days_delta=-1.0,
        historical_delay_avg_days=0.5,
        historical_defect_rate=0.01,
        payment_terms_penalty=0.0,
        warranty_months=24.0,
        category_experience_years=5.0,
        extraction_completeness_pct=1.0,
        anomaly_lowball_flag=0.0,
    )

    response = shap_engine.evaluate_and_explain(
        supplier_id="sup_test_001", quote_id="q_test_001", feature_vector=features
    )

    # 1. Assert Response Basic Properties
    assert response.supplier_id == "sup_test_001"
    assert response.quote_id == "q_test_001"

    # 2. Assert Score Range Boundaries
    assert 0.0 <= response.final_score <= 100.0
    assert response.baseline_score > 0.0

    # 3. Assert SHAP Drivers are Populated
    breakdown = response.shap_breakdown
    assert isinstance(breakdown.top_positive_drivers, list)
    assert isinstance(breakdown.top_negative_drivers, list)


def test_cold_start_new_supplier_handling(shap_engine):
    """Test cold-start handling when historical delay and defect metrics are None."""
    features = FeatureVector(
        price_variance_pct=0.0,
        tco_markup_pct=0.05,
        lead_time_days_delta=0.0,
        historical_delay_avg_days=None,  # Cold-start missing value
        historical_defect_rate=None,  # Cold-start missing value
        payment_terms_penalty=0.5,
        warranty_months=12.0,
        category_experience_years=1.0,
        extraction_completeness_pct=0.9,
        anomaly_lowball_flag=0.0,
    )

    # Should execute smoothly without raising TypeError or NaN errors
    response = shap_engine.evaluate_and_explain(
        supplier_id="sup_new_002", quote_id="q_new_002", feature_vector=features
    )

    assert response.final_score >= 0.0
    assert response.supplier_id == "sup_new_002"


def test_anomaly_lowball_flag_impact(shap_engine):
    """Test that setting anomaly_lowball_flag negatively impacts the score delta."""
    features = FeatureVector(
        price_variance_pct=-0.25,  # Suspiciously cheap
        tco_markup_pct=0.0,
        lead_time_days_delta=0.0,
        historical_delay_avg_days=0.0,
        historical_defect_rate=0.0,
        payment_terms_penalty=0.0,
        warranty_months=12.0,
        category_experience_years=2.0,
        extraction_completeness_pct=1.0,
        anomaly_lowball_flag=1.0,  # Trigger low-ball flag
    )

    response = shap_engine.evaluate_and_explain(
        supplier_id="sup_lowball_003",
        quote_id="q_lowball_003",
        feature_vector=features,
    )

    # Check that low-ball anomaly exists in negative drivers
    negative_driver_names = [
        driver.feature_name
        for driver in response.shap_breakdown.top_negative_drivers
    ]
    assert "anomaly_lowball_flag" in negative_driver_names