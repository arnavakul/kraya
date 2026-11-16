import json
from types import SimpleNamespace

import pytest

from agents.inbox_triage.agent import run_inbox_triage_agent
from agents.quote_extraction.agent import QuoteExtractionAgent
from agents.supplier_intent.agent import SupplierIntentAgent
from pydantic_models.email_classification import EmailClassification
from pydantic_models.email_message import EmailAttachment, EmailMessage
from schemas.suppliers_intent import (
    RecommendedAction,
    SupplierIntent,
    SupplierIntentAnalysis,
)


class FakeInboxRepository:
    def __init__(self):
        self.completed = {}
        self.failed = {}

    def claim_email(self, email):
        return True

    def complete_email(self, email_id, result):
        self.completed[email_id] = result
        return True

    def fail_email(self, email_id, error_message):
        self.failed[email_id] = error_message
        return True


class OneEmailConnector:
    def __init__(self, email):
        self.email = email

    def fetch_emails(self):
        return [self.email]


def make_email(category, *, body=None, attachments=None):
    return EmailMessage(
        email_id="SYNTHETIC-EMAIL-1",
        sender_email="vendor@example.test",
        sender_name="Synthetic Vendor",
        subject=(
            "Laptop quotation RFQ-TEST"
            if category == "quotation"
            else "Question about RFQ-TEST"
        ),
        body=body or "Please confirm the delivery lead time.",
        thread_id="SYNTHETIC-THREAD-1",
        in_reply_to="SYNTHETIC-REPLY-1",
        attachments=attachments or [],
    )


def fake_classifier(category):
    def classify(email, security_result):
        return EmailClassification(
            category=category,
            confidence=0.98,
            summary=f"Synthetic {category} message.",
            classification_source="llm",
        )

    return classify


def fake_llm(response_data):
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(response_data))
            )
        ]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: response
            )
        )
    )


def quotation_payload(*, invalid=False):
    total = 199 if invalid else 200
    return {
        "supplier_name": "Synthetic Vendor",
        "supplier_email": "vendor@example.test",
        "quotation_number": "Q-TEST-1",
        "issue_date": "2026-11-01",
        "valid_until": "2026-12-01",
        "currency": "INR",
        "line_items": [
            {
                "product_name": "Laptop",
                "quantity": 2,
                "unit_price": 100,
                "line_total": total,
                "taxes": [],
            }
        ],
        "subtotal": total,
        "taxes": [],
        "shipping_cost": 0,
        "shipping_status": "included",
        "discount": 0,
        "grand_total": total,
        "delivery_time_days": 10,
        "delivery_time_unit": "calendar_days",
        "warranty_period": "2 years",
        "payment_terms": "Net 30 days",
    }


def run_triage(monkeypatch, email, category, **kwargs):
    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        fake_classifier(category),
    )
    repository = FakeInboxRepository()
    result = run_inbox_triage_agent(
        connector=OneEmailConnector(email),
        repository=repository,
        **kwargs,
    )
    return result, repository


def test_quotation_message_runs_agent6_and_returns_financial_report(monkeypatch):
    monkeypatch.setattr(
        "agents.quote_extraction.extractor.get_llm_client",
        lambda: fake_llm(quotation_payload()),
    )
    email = make_email(
        "quotation",
        body="Synthetic supplier quotation: two laptops at INR 100 each.",
    )
    quote_agent = QuoteExtractionAgent(quotation_repository=object())

    result, repository = run_triage(
        monkeypatch,
        email,
        "quotation",
        quote_extraction_agent=quote_agent,
    )

    outcome = result.quotation_processing_results[0]
    assert outcome.email_id == email.email_id
    assert outcome.thread_id == email.thread_id
    assert outcome.in_reply_to == email.in_reply_to
    assert outcome.status == "completed"
    assert outcome.quotation["grand_total"] == "200"
    assert outcome.financial_validation["status"] == "VALID"
    assert repository.completed[email.email_id].routing_action == (
        "quotation_processing"
    )
    assert quote_agent.quotation_repository is not None


def test_clarification_message_runs_agent7_with_available_context(monkeypatch):
    monkeypatch.setattr(
        "agents.supplier_intent.analyzer.get_llm_client",
        lambda: fake_llm(
            {
                "intent": "needs_clarification",
                "intent_summary": "Supplier asks about delivery terms.",
                "missing_information": ["delivery lead time"],
                "supplier_questions": ["What is the delivery location?"],
                "clarification_questions": [
                    "Please confirm the expected lead time."
                ],
                "recommended_action": "request_information",
                "requires_human_review": True,
            }
        ),
    )
    email = make_email("question")
    intent_agent = SupplierIntentAgent(inbox_repository=object())

    result, repository = run_triage(
        monkeypatch,
        email,
        "question",
        supplier_intent_agent=intent_agent,
    )

    outcome = result.supplier_intent_results[0]
    assert outcome.status == "completed"
    assert outcome.analysis.intent == SupplierIntent.NEEDS_CLARIFICATION
    assert outcome.analysis.missing_information == ["delivery lead time"]
    assert outcome.analysis.clarification_questions == [
        "Please confirm the expected lead time."
    ]
    assert outcome.analysis.recommended_action == (
        RecommendedAction.REQUEST_INFORMATION
    )
    assert outcome.requires_human_review is True
    assert repository.completed[email.email_id].requires_human_review is True


def test_attachment_metadata_without_content_is_flagged_for_review(monkeypatch):
    monkeypatch.setattr(
        "agents.quote_extraction.extractor.get_llm_client",
        lambda: fake_llm(quotation_payload()),
    )
    email = make_email(
        "quotation",
        body="Please find our quotation attached.",
        attachments=[EmailAttachment(filename="quote.pdf")],
    )

    result, repository = run_triage(
        monkeypatch,
        email,
        "quotation",
        quote_extraction_agent=QuoteExtractionAgent(
            quotation_repository=object()
        ),
    )

    outcome = result.quotation_processing_results[0]
    assert outcome.status == "needs_review"
    assert outcome.requires_human_review is True
    assert any(
        "Attachment content is unavailable" in warning
        for warning in outcome.financial_validation["warnings"]
    )
    assert repository.completed[email.email_id].requires_human_review is True


def test_invalid_quotation_is_returned_with_validation_errors(monkeypatch):
    monkeypatch.setattr(
        "agents.quote_extraction.extractor.get_llm_client",
        lambda: fake_llm(quotation_payload(invalid=True)),
    )

    result, _ = run_triage(
        monkeypatch,
        make_email("quotation"),
        "quotation",
        quote_extraction_agent=QuoteExtractionAgent(
            quotation_repository=object()
        ),
    )

    outcome = result.quotation_processing_results[0]
    assert outcome.status == "needs_review"
    assert outcome.financial_validation["status"] == "INVALID"
    assert outcome.financial_validation["errors"]
    assert outcome.requires_human_review is True


def test_unclear_supplier_intent_requires_human_review(monkeypatch):
    monkeypatch.setattr(
        "agents.supplier_intent.analyzer.get_llm_client",
        lambda: fake_llm(
            {
                "intent": "unclear",
                "intent_summary": "The message is ambiguous.",
                "recommended_action": "no_action",
                "requires_human_review": False,
            }
        ),
    )

    result, repository = run_triage(
        monkeypatch,
        make_email("question"),
        "question",
        supplier_intent_agent=SupplierIntentAgent(
            inbox_repository=object()
        ),
    )

    outcome = result.supplier_intent_results[0]
    assert outcome.analysis.intent == SupplierIntent.UNCLEAR
    assert outcome.analysis.requires_human_review is True
    assert outcome.requires_human_review is True
    assert repository.completed[outcome.email_id].requires_human_review is True


@pytest.mark.parametrize("route", ["quotation", "question"])
def test_agent_failure_is_structured_and_escalated(monkeypatch, route):
    class FailingAgent:
        def process_text(self, text):
            raise RuntimeError("synthetic extraction failure")

        def process_message(self, **kwargs):
            raise RuntimeError("synthetic intent failure")

    email = make_email(route)
    kwargs = (
        {"quote_extraction_agent": FailingAgent()}
        if route == "quotation"
        else {"supplier_intent_agent": FailingAgent()}
    )

    result, repository = run_triage(
        monkeypatch,
        email,
        route,
        **kwargs,
    )

    outcomes = (
        result.quotation_processing_results
        if route == "quotation"
        else result.supplier_intent_results
    )
    assert outcomes[0].status == "failed"
    assert outcomes[0].requires_human_review is True
    assert "synthetic" in outcomes[0].error
    assert result.total_failed == 0
    assert repository.completed[email.email_id].requires_human_review is True


def test_non_agent_route_preserves_existing_routing(monkeypatch):
    class MustNotRun:
        def process_text(self, text):
            raise AssertionError("Agent 6 should not run for rejection")

        def process_message(self, **kwargs):
            raise AssertionError("Agent 7 should not run for rejection")

    email = make_email("rejection")
    result, repository = run_triage(
        monkeypatch,
        email,
        "rejection",
        quote_extraction_agent=MustNotRun(),
        supplier_intent_agent=MustNotRun(),
    )

    assert result.processed_emails[0].routing_action == (
        "supplier_response_update"
    )
    assert not result.quotation_processing_results
    assert not result.supplier_intent_results
    assert repository.completed[email.email_id].category == "rejection"

