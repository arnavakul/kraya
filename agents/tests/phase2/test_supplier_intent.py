
from types import SimpleNamespace

import pytest

from agents.supplier_intent.analyzer import (
    SupplierIntentError,
    analyze_supplier_message,
    normalize_response,
)


def test_normalize_response_maps_aliases():
    data = {
        "supplier_intent": "interested",
        "summary": "Supplier is interested.",
        "provided_information": ["Product available"],
        "missing_fields": ["Delivery date"],
        "questions_asked": ["What is the delivery location?"],
        "next_action": "request_information",
        "questions_to_ask": ["Please confirm delivery time."],
    }

    result = normalize_response(data)

    assert result["intent"] == "interested"
    assert result["supplier_questions"] == [
        "What is the delivery location?"
    ]
    assert result["clarification_questions"] == [
        "Please confirm delivery time."
    ]


def test_normalize_response_sets_defaults():
    result = normalize_response({})

    assert result["intent"] == "unclear"
    assert result["recommended_action"] == "no_action"
    assert result["mentioned_details"] == []
    assert result["missing_information"] == []
    assert result["requires_human_review"] is False


def test_empty_supplier_message_raises_error():
    with pytest.raises(ValueError):
        analyze_supplier_message("   ")


def test_analyze_supplier_message_with_mocked_llm(monkeypatch):
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"intent":"interested",'
                    '"intent_summary":"Supplier is interested.",'
                    '"recommended_action":"no_action"}'
                )
            )
        ]
    )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: fake_response
            )
        )
    )

    monkeypatch.setattr(
        "agents.supplier_intent.analyzer.get_llm_client",
        lambda: fake_client,
    )

    result = analyze_supplier_message(
        supplier_message="We are interested in your RFQ."
    )

    assert result.intent.value == "interested"
    assert result.recommended_action.value == "no_action"


from unittest.mock import Mock

from agents.supplier_intent.agent import SupplierIntentAgent
from schemas.suppliers_intent import (
    SupplierIntent,
    RecommendedAction,
    SupplierIntentAnalysis,
)


def test_process_and_save():
    mock_repository = Mock()

    mock_repository.save_analysis.return_value = {
        "email_id": "test-email-001"
    }

    agent = SupplierIntentAgent(
        inbox_repository=mock_repository
    )

    expected_analysis = SupplierIntentAnalysis(
        intent=SupplierIntent.INTERESTED,
        intent_summary="Supplier is interested.",
        recommended_action=RecommendedAction.NO_ACTION,
    )

    agent.process_message = Mock(return_value=expected_analysis)

    result = agent.process_and_save(
        email_id="test-email-001",
        supplier_message="We are interested in your RFQ.",
    )

    assert result == expected_analysis

    mock_repository.update_processing_status.assert_called_once_with(
        email_id="test-email-001",
        status="processing",
    )

    mock_repository.save_analysis.assert_called_once_with(
        email_id="test-email-001",
        analysis=expected_analysis,
    )
