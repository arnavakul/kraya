from datetime import date, timedelta
import subprocess
import sys
import textwrap

import pytest

from agents.evaluation.agent import EvaluationAgent
from agents.evaluation.ml_client import MLEvaluationClient
from orchestration.inbox_triage_nodes import evaluation_node
from pydantic_models.inbox_triage_result import (
    InboxTriageRunResult,
    QuotationProcessingResult,
)
from schemas.evaluation import MLEvaluationStatus
from schemas.ml_evaluation import EvaluationResponse, FeatureVector
from schemas.quotation import Quotation, DeliveryTimeUnit


def make_quote(name="Synthetic Supplier", **overrides):
    values = {
        "supplier_name": name,
        "supplier_email": f"{name.lower().replace(' ', '.')}@example.test",
        "quotation_number": f"Q-{name.split()[0]}",
        "issue_date": date.today(),
        "valid_until": date.today() + timedelta(days=30),
        "currency": "INR",
        "grand_total": 1000,
        "delivery_time_days": 10,
        "delivery_time_unit": DeliveryTimeUnit.CALENDAR_DAYS,
        "warranty_period": "3 years",
        "payment_terms": "Net 30 days",
    }
    values.update(overrides)
    return Quotation(**values)


class RecordingEvaluationAgent:
    def __init__(self):
        self.quotations = None
        self.context = None

    async def evaluate_suppliers_with_ml(self, quotations, ml_context=None):
        self.quotations = quotations
        self.context = ml_context
        from schemas.evaluation import EvaluationResult

        return EvaluationResult(evaluations=[])


def test_only_completed_validated_quotes_reach_agent8():
    valid = make_quote().model_dump(mode="json")
    triage_result = InboxTriageRunResult(
        quotation_processing_results=[
            QuotationProcessingResult(
                email_id="email-1",
                sender_email="supplier@example.test",
                status="completed",
                quotation=valid,
            ),
            QuotationProcessingResult(
                email_id="email-2",
                sender_email="review@example.test",
                status="needs_review",
                quotation=make_quote("Review Supplier").model_dump(mode="json"),
            ),
        ]
    )
    agent = RecordingEvaluationAgent()

    result = evaluation_node({
        "inbox_triage_result": triage_result,
        "evaluation_agent": agent,
        "evaluation_ml_context": {},
    })

    assert len(agent.quotations) == 1
    assert agent.quotations[0].supplier_name == "Synthetic Supplier"
    assert result["evaluation_status"] == "completed"
    assert result["evaluation_source_messages"][0]["email_id"] == "email-1"


class HighScoreMLClient:
    async def health_check(self):
        return True

    async def evaluate_supplier(self, supplier_id, quote_id, features):
        assert supplier_id == "supplier-1"
        assert quote_id == "quote-1"
        return EvaluationResponse(
            supplier_id=supplier_id,
            quote_id=quote_id,
            final_score=100,
            baseline_score=50,
            shap_breakdown={
                "base_value": 50,
                "top_positive_drivers": [],
                "top_negative_drivers": [],
            },
        )


class FakeExplainer:
    def explain(self, evaluation_data):
        names = [item["supplier_name"] for item in evaluation_data["suppliers"]]
        return {
            "supplier_strengths": {name: [] for name in names},
            "supplier_weaknesses": {name: [] for name in names},
            "trade_offs": {name: [] for name in names},
            "recommendation_summary": "Synthetic test evaluation.",
            "recommendation_reasoning": [],
        }


@pytest.mark.asyncio
async def test_mandatory_failure_stays_ineligible_despite_high_ml_score():
    agent = EvaluationAgent(ml_client=HighScoreMLClient(), evaluation_repository=object())
    agent.explainer = FakeExplainer()
    quote = make_quote(warranty_period="6 months")
    context = {
        "Synthetic Supplier": {
            "supplier_id": "supplier-1",
            "quote_id": "quote-1",
            "market_benchmark_price": 1100,
            "shipping_and_hidden_costs": 0,
            "historical_delay_avg_days": 0,
            "historical_defect_rate": 0,
            "payment_terms_penalty": 0,
            "category_experience_years": 2,
        }
    }

    result = await agent.evaluate_suppliers_with_ml(
        [quote], min_warranty_years=2, ml_context=context
    )

    evaluated = result.evaluations[0]
    assert evaluated.ml_score == 100
    assert evaluated.mandatory_constraints["warranty"].value == "fail"
    assert evaluated.eligible is False
    assert result.recommended_supplier is None


@pytest.mark.asyncio
async def test_missing_verified_ml_features_skip_client_call():
    class MustNotCall:
        async def health_check(self):
            raise AssertionError("ML must be skipped when evidence is missing")

    agent = EvaluationAgent(ml_client=MustNotCall(), evaluation_repository=object())
    agent.explainer = FakeExplainer()
    result = await agent.evaluate_suppliers_with_ml(
        [make_quote()],
        ml_context={"Synthetic Supplier": {"supplier_id": "s-1", "quote_id": "q-1"}},
    )

    assert result.evaluations[0].ml_status == MLEvaluationStatus.SKIPPED_MISSING_FEATURES
    assert result.evaluations[0].ml_missing_features


def test_multiple_suppliers_are_returned_by_agent8():
    agent = EvaluationAgent(ml_client=HighScoreMLClient(), evaluation_repository=object())
    agent.explainer = FakeExplainer()
    result = agent.evaluate_suppliers([
        make_quote("Supplier One"),
        make_quote("Supplier Two", grand_total=1200),
    ])
    assert {item.supplier_name for item in result.evaluations} == {
        "Supplier One", "Supplier Two"
    }


def test_ml_client_asgi_contract_round_trip_is_bounded():
    # The ASGI integration has hung in this environment even with HTTPX's
    # timeout; isolate it in a child process so the test itself has a hard cap.
    script = textwrap.dedent("""
        import asyncio
        from main import app
        import evaluation.router as evaluation_router
        from agents.evaluation.ml_client import MLEvaluationClient
        from schemas.ml_evaluation import EvaluationResponse, FeatureVector

        class FakeEngine:
            def evaluate_and_explain(self, supplier_id, quote_id, feature_vector):
                assert list(feature_vector.model_dump()) == [
                    "price_variance_pct", "tco_markup_pct",
                    "lead_time_days_delta", "historical_delay_avg_days",
                    "historical_defect_rate", "payment_terms_penalty",
                    "warranty_months", "category_experience_years",
                    "extraction_completeness_pct", "anomaly_lowball_flag",
                ]
                return EvaluationResponse(
                    supplier_id=supplier_id, quote_id=quote_id,
                    final_score=77, baseline_score=70,
                    shap_breakdown={"base_value": 70,
                        "top_positive_drivers": [], "top_negative_drivers": []},
                )

        evaluation_router.eval_engine = FakeEngine()
        features = FeatureVector(
            price_variance_pct=-0.05, tco_markup_pct=0.02,
            lead_time_days_delta=0, historical_delay_avg_days=2,
            historical_defect_rate=0.01, payment_terms_penalty=0,
            warranty_months=36, category_experience_years=5,
            extraction_completeness_pct=1, anomaly_lowball_flag=0,
        )

        async def run():
            client = MLEvaluationClient(app=app, timeout=2.0)
            response = await client.evaluate_supplier(
                "supplier-test", "quote-test", features
            )
            assert response.supplier_id == "supplier-test"
            assert response.quote_id == "quote-test"
            assert response.final_score == 77

        asyncio.run(run())
    """)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
