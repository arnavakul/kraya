
from pydantic_models.email_message import EmailMessage
from pydantic_models.email_classification import EmailClassification
from schemas.suppliers_intent import (
    RecommendedAction,
    SupplierIntent,
    SupplierIntentAnalysis,
)

from orchestration.inbox_triage_graph import inbox_triage_graph
from schemas.quotation import Quotation
from services.financial_validator import (
    ValidationReport,
    ValidationStatus,
)


class FakeQuoteExtractionAgent:
    def process_text(self, document_text):
        return {
            "quotation": Quotation(
                supplier_name="Synthetic Supplier",
                currency="INR",
            ),
            "validation_report": ValidationReport(
                status=ValidationStatus.VALID,
            ),
        }


class FakeSupplierIntentAgent:
    def process_message(self, **kwargs):
        raise AssertionError("A quotation must not enter clarification.")


class FakeEvaluationAgent:
    async def evaluate_suppliers_with_ml(self, quotations, ml_context=None):
        from schemas.evaluation import EvaluationResult

        return EvaluationResult(evaluations=[])


def fake_agents():
    return {
        "quote_extraction_agent": FakeQuoteExtractionAgent(),
        "supplier_intent_agent": FakeSupplierIntentAgent(),
        "evaluation_agent": FakeEvaluationAgent(),
    }


class FakeEmailConnector:

    def fetch_emails(self):
        return [
            EmailMessage(
                email_id="GRAPH-001",
                sender_email="supplier@example.com",
                subject="Laptop quotation",
                body="Please find our quotation for 20 laptops."
            )
        ]


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


def mock_classifier(email, security_result):

    return EmailClassification(
        category="quotation",
        confidence=0.96,
        summary="Supplier submitted a laptop quotation.",
        classification_source="llm"
    )


def test_graph_executes_inbox_triage(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classifier
    )

    repository = FakeInboxRepository()

    result = inbox_triage_graph.invoke({
        "connector": FakeEmailConnector(),
        "repository": repository,
        **fake_agents(),
    })

    assert result["inbox_triage_status"] == "completed"
    assert result["inbox_triage_result"].total_processed == 1


def test_graph_persists_triage_result(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classifier
    )

    repository = FakeInboxRepository()

    result = inbox_triage_graph.invoke({
        "connector": FakeEmailConnector(),
        "repository": repository,
        **fake_agents(),
    })

    assert "GRAPH-001" in repository.completed

    saved_result = repository.completed["GRAPH-001"]

    assert saved_result.category == "quotation"
    assert saved_result.routing_action == "quotation_processing"


def test_graph_passes_clarification_to_agent7(monkeypatch):
    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        lambda email, security_result: EmailClassification(
            category="question",
            confidence=0.96,
            summary="Supplier asks a clarification question.",
            classification_source="llm",
        ),
    )

    class FakeIntentAgent:
        def __init__(self):
            self.call = None

        def process_message(self, **kwargs):
            self.call = kwargs
            return SupplierIntentAnalysis(
                intent=SupplierIntent.NEEDS_CLARIFICATION,
                intent_summary="Delivery details are unclear.",
                missing_information=["delivery lead time"],
                clarification_questions=[
                    "Please confirm the expected delivery lead time."
                ],
                recommended_action=RecommendedAction.REQUEST_INFORMATION,
                requires_human_review=True,
            )

    repository = FakeInboxRepository()
    intent_agent = FakeIntentAgent()

    class QuestionConnector:
        def fetch_emails(self):
            return [
                EmailMessage(
                    email_id="GRAPH-QUESTION-001",
                    sender_email="supplier@example.com",
                    subject="Clarification about laptop warranty",
                    body="Could you confirm whether warranty is onsite?",
                    thread_id="GRAPH-THREAD-QUESTION-001",
                )
            ]

    result = inbox_triage_graph.invoke({
        "connector": QuestionConnector(),
        "repository": repository,
        "supplier_intent_agent": intent_agent,
    })

    outcome = result[
        "inbox_triage_result"
    ].supplier_intent_results[0]
    assert intent_agent.call["supplier_message"].startswith(
        "Could you confirm"
    )
    assert intent_agent.call["rfq_context"] == (
        "Clarification about laptop warranty"
    )
    assert intent_agent.call["conversation_history"] == ""
    assert outcome.analysis.recommended_action == (
        RecommendedAction.REQUEST_INFORMATION
    )
    assert result["inbox_triage_result"].processed_emails[0].requires_human_review


def test_graph_reports_agent6_failure_for_review(monkeypatch):
    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classifier,
    )

    class FailingQuoteAgent:
        def process_text(self, document_text):
            raise RuntimeError("synthetic extraction failure")

    result = inbox_triage_graph.invoke({
        "connector": FakeEmailConnector(),
        "repository": FakeInboxRepository(),
        "quote_extraction_agent": FailingQuoteAgent(),
        "supplier_intent_agent": FakeSupplierIntentAgent(),
    })

    assert result["inbox_triage_status"] == "partial"
    assert result["errors"] == ["synthetic extraction failure"]
    assert result["inbox_triage_result"].processed_emails[0].requires_human_review


def test_graph_handles_duplicate_email(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classifier
    )

    class DuplicateRepository(FakeInboxRepository):

        def claim_email(self, email):
            return False

    result = inbox_triage_graph.invoke({
        "connector": FakeEmailConnector(),
        "repository": DuplicateRepository()
    })

    assert result["inbox_triage_status"] == "completed"
    assert result["inbox_triage_result"].total_skipped == 1
    assert result["inbox_triage_result"].total_processed == 0


def test_graph_handles_empty_inbox():

    class EmptyConnector:

        def fetch_emails(self):
            return []

    result = inbox_triage_graph.invoke({
        "connector": EmptyConnector(),
        "repository": FakeInboxRepository()
    })

    assert result["inbox_triage_status"] == "completed"
    assert result["inbox_triage_result"].total_fetched == 0


def test_graph_handles_claim_failure():

    class FailingRepository(FakeInboxRepository):

        def claim_email(self, email):
            raise RuntimeError("Database unavailable")

    result = inbox_triage_graph.invoke({
        "connector": FakeEmailConnector(),
        "repository": FailingRepository()
    })

    assert result["inbox_triage_status"] == "failed"
    assert result["inbox_triage_result"].total_failed == 1
