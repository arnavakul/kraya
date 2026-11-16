
from datetime import date, timedelta

import pytest
import httpx
from main import app
from schemas.ml_evaluation import FeatureVector, EvaluationResponse
from schemas.quotation import DeliveryTimeUnit, Quotation, QuoteLineItem
from schemas.evaluation import MLEvaluationStatus
from agents.evaluation.ml_client import MLEvaluationClient
from agents.evaluation.agent import EvaluationAgent
from agents.evaluation.feature_builder import EvaluationFeatureBuilder


@pytest.mark.asyncio
async def test_fastapi_health_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "UP", "service": "kraya-agents"}


@pytest.mark.asyncio
async def test_fastapi_evaluation_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        features = FeatureVector(
            price_variance_pct=-0.05,
            tco_markup_pct=0.02,
            lead_time_days_delta=0.0,
            historical_delay_avg_days=2.5,
            historical_defect_rate=0.01,
            payment_terms_penalty=0.0,
            warranty_months=36.0,
            category_experience_years=5.0,
            extraction_completeness_pct=1.0,
            anomaly_lowball_flag=0.0,
        )
        response = await client.post(
            "/evaluations/score-and-explain",
            params={"supplier_id": "sup-001", "quote_id": "quote-001"},
            json=features.model_dump(mode="json"),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["supplier_id"] == "sup-001"
        assert data["quote_id"] == "quote-001"
        assert 0.0 <= data["final_score"] <= 100.0
        assert "shap_breakdown" in data
        assert isinstance(data["shap_breakdown"]["base_value"], float)
        assert isinstance(data["shap_breakdown"]["top_positive_drivers"], list)
        assert isinstance(data["shap_breakdown"]["top_negative_drivers"], list)


@pytest.mark.asyncio
async def test_ml_client_with_fastapi_app():
    client = MLEvaluationClient(app=app)
    assert await client.health_check() is True

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
    assert isinstance(result, EvaluationResponse)
    assert 0 <= result.final_score <= 100
    assert result.supplier_id == "sup_001"
    assert result.quote_id == "quote_001"


@pytest.mark.asyncio
async def test_agent8_full_integration_with_ml():
    client = MLEvaluationClient(app=app)
    agent = EvaluationAgent(ml_client=client)

    quotation = Quotation(
        supplier_name="Alpha Tech",
        supplier_email="alpha@example.com",
        issue_date=date.today(),
        valid_until=date.today() + timedelta(days=30),
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Server Rack",
                quantity=2,
                unit_price=250000,
                line_total=500000,
            )
        ],
        subtotal=500000,
        grand_total=500000,
        delivery_time_days=10,
        delivery_time_unit=DeliveryTimeUnit.CALENDAR_DAYS,
        warranty_period="3 years",
        payment_terms="Net 30 days",
    )

    ml_context = {
        "Alpha Tech": {
            "supplier_id": "sup-101",
            "quote_id": "quote-101",
            "market_benchmark_price": 520000.0,
            "shipping_and_hidden_costs": 10000.0,
            "historical_delay_avg_days": 1.2,
            "historical_defect_rate": 0.005,
            "payment_terms_penalty": 0.0,
            "category_experience_years": 7.0,
            "anomaly_lowball_flag": 0.0,
        }
    }

    result = await agent.evaluate_suppliers_with_ml(
        quotations=[quotation],
        max_delivery_days=15,
        min_warranty_years=2,
        min_validity_days=15,
        required_specs=["Server Rack"],
        ml_context=ml_context,
    )

    assert len(result.evaluations) == 1
    eval_record = result.evaluations[0]
    assert eval_record.supplier_name == "Alpha Tech"
    assert eval_record.eligible is True
    assert eval_record.ml_status == MLEvaluationStatus.COMPLETED
    assert eval_record.ml_score is not None
    assert 0.0 <= eval_record.ml_score <= 100.0
    assert eval_record.ml_shap_breakdown is not None
    assert result.recommended_supplier == "Alpha Tech"


@pytest.mark.asyncio
async def test_agent8_skips_ml_when_features_missing():
    client = MLEvaluationClient(app=app)
    agent = EvaluationAgent(ml_client=client)

    quotation = Quotation(
        supplier_name="Beta Corp",
        supplier_email="beta@example.com",
        currency="INR",
        line_items=[
            QuoteLineItem(
                product_name="Server Rack",
                quantity=1,
                unit_price=100000,
                line_total=100000,
            )
        ],
        subtotal=100000,
        grand_total=100000,
        delivery_time_days=10,
        warranty_period="1 year",
        payment_terms="Advance",
    )

    # Empty context: missing market_benchmark_price, history, etc.
    ml_context = {
        "Beta Corp": {
            "supplier_id": "sup-102",
            "quote_id": "quote-102",
        }
    }

    result = await agent.evaluate_suppliers_with_ml(
        quotations=[quotation],
        max_delivery_days=20,
        min_warranty_years=1,
        min_validity_days=15,
        ml_context=ml_context,
    )

    eval_record = result.evaluations[0]
    assert eval_record.ml_status == MLEvaluationStatus.SKIPPED_MISSING_FEATURES
    assert len(eval_record.ml_missing_features) > 0
    # Deterministic evaluation is preserved!
    assert eval_record.weighted_score > 0
