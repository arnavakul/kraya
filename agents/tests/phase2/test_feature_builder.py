
from decimal import Decimal

from agents.evaluation.feature_builder import EvaluationFeatureBuilder
from schemas.quotation import (
    Quotation,
    DeliveryTimeUnit,
)


def test_missing_data_skips_ml():
    quotation = Quotation(supplier_name="Demo Supplier")

    result = EvaluationFeatureBuilder().build(quotation)

    assert result.ready_for_ml is False
    assert result.features is None
    assert "price_variance_pct" in result.missing_features
    assert "historical_delay_avg_days" in result.missing_features


def test_complete_data_allows_ml():
    quotation = Quotation(
        supplier_name="Demo Supplier",
        currency="INR",
        grand_total=Decimal("100000"),
        shipping_cost=Decimal("2000"),
        delivery_time_days=15,
        delivery_time_unit=DeliveryTimeUnit.CALENDAR_DAYS,
        warranty_period="2 years",
        payment_terms="Net 30 days",
    )

    result = EvaluationFeatureBuilder().build(
        quotation=quotation,
        target_lead_time_days=20,
        market_benchmark_price=Decimal("110000"),
        shipping_and_hidden_costs=Decimal("2000"),
        historical_delay_avg_days=2.5,
        historical_defect_rate=0.02,
        payment_terms_penalty=0.0,
        category_experience_years=4.0,
    )

    assert result.ready_for_ml is True
    assert result.features is not None
    assert result.missing_features == []
    assert result.features.warranty_months == 24.0
    assert result.features.lead_time_days_delta == -5.0


def test_invalid_supplier_history_skips_ml():
    quotation = Quotation(
        supplier_name="Demo Supplier",
        grand_total=Decimal("100000"),
        delivery_time_days=15,
        delivery_time_unit=DeliveryTimeUnit.CALENDAR_DAYS,
        warranty_period="2 years",
    )

    result = EvaluationFeatureBuilder().build(
        quotation=quotation,
        target_lead_time_days=20,
        market_benchmark_price=Decimal("110000"),
        shipping_and_hidden_costs=Decimal("2000"),
        historical_delay_avg_days=-1,
        historical_defect_rate=1.5,
        payment_terms_penalty=0.0,
        category_experience_years=4.0,
    )

    assert result.ready_for_ml is False
    assert "historical_delay_avg_days" in result.missing_features
    assert "historical_defect_rate" in result.missing_features
