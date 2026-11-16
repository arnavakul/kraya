import pytest
from main import app
from schemas.ml_evaluation import FeatureVector
from agents.evaluation.ml_client import MLEvaluationClient


@pytest.mark.asyncio
async def test_ml_client_connection():
    client = MLEvaluationClient(app=app)

    features = FeatureVector(
        price_variance_pct=-0.045,
        tco_markup_pct=0.02,
        lead_time_days_delta=0.0,
        historical_delay_avg_days=3.8,
        historical_defect_rate=0.01,
        payment_terms_penalty=0.05,
        warranty_months=36.0,
        category_experience_years=4.5,
        extraction_completeness_pct=0.95,
        anomaly_lowball_flag=0.0,
    )

    result = await client.evaluate_supplier(
        supplier_id="sup_001",
        quote_id="quote_001",
        features=features,
    )

    assert 0 <= result.final_score <= 100
    assert result.supplier_id == "sup_001"