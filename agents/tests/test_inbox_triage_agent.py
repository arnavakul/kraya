
from pydantic_models.email_classification import EmailClassification

from agents.inbox_triage.agent import run_inbox_triage_agent
from tools.inbox.mock_email_connector import MockEmailConnector
from schemas.quotation import Quotation
from schemas.suppliers_intent import (
    RecommendedAction,
    SupplierIntent,
    SupplierIntentAnalysis,
)
from services.financial_validator import (
    ValidationReport,
    ValidationStatus,
)


class FakeInboxRepository:

    def __init__(self, duplicate_ids=None):
        self.claimed_ids = set()
        self.duplicate_ids = set(duplicate_ids or [])
        self.completed = {}
        self.failed = {}

    def claim_email(self, email):

        if email.email_id in self.duplicate_ids:
            return False

        if email.email_id in self.claimed_ids:
            return False

        self.claimed_ids.add(email.email_id)
        return True

    def complete_email(self, email_id, result):

        self.completed[email_id] = result
        return True

    def fail_email(self, email_id, error_message):

        self.failed[email_id] = error_message
        return True


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
        return SupplierIntentAnalysis(
            intent=SupplierIntent.INTERESTED,
            intent_summary="Supplier is interested.",
            recommended_action=RecommendedAction.NO_ACTION,
        )


def fake_agents():
    return {
        "quote_extraction_agent": FakeQuoteExtractionAgent(),
        "supplier_intent_agent": FakeSupplierIntentAgent(),
    }


def mock_classify_email(email, security_result):

    categories = {
        "EMAIL-001": "quotation",
        "EMAIL-002": "question",
        "EMAIL-003": "rejection",
        "EMAIL-004": "follow_up",
        "EMAIL-005": "spam",
        "EMAIL-006": "out_of_office",
    }

    if security_result.is_suspicious:
        return EmailClassification(
            category="suspicious",
            confidence=None,
            summary="Security screening flagged this email.",
            classification_source="security_rule"
        )

    return EmailClassification(
        category=categories[email.email_id],
        confidence=0.95,
        summary=f"Classified {email.email_id}",
        classification_source="llm"
    )


def test_agent_processes_all_emails(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classify_email
    )

    repository = FakeInboxRepository()

    result = run_inbox_triage_agent(
        repository=repository,
        **fake_agents(),
    )

    assert result.total_fetched == 7
    assert result.total_processed == 7
    assert result.total_skipped == 0
    assert result.total_failed == 0


def test_agent_routes_all_categories(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classify_email
    )

    result = run_inbox_triage_agent(
        repository=FakeInboxRepository(),
        **fake_agents(),
    )

    categories = [
        item.category for item in result.processed_emails
    ]

    assert categories == [
        "quotation",
        "question",
        "rejection",
        "follow_up",
        "spam",
        "out_of_office",
        "suspicious"
    ]


def test_suspicious_email_goes_to_security_review(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classify_email
    )

    result = run_inbox_triage_agent(
        repository=FakeInboxRepository(),
        **fake_agents(),
    )

    suspicious = next(
        item for item in result.processed_emails
        if item.email_id == "EMAIL-007"
    )

    assert suspicious.category == "suspicious"
    assert suspicious.routing_action == "security_review"
    assert suspicious.requires_human_review is True


def test_duplicate_emails_are_skipped(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classify_email
    )

    repository = FakeInboxRepository(
        duplicate_ids=["EMAIL-001", "EMAIL-002"]
    )

    result = run_inbox_triage_agent(
        repository=repository,
        **fake_agents(),
    )

    assert result.total_skipped == 2
    assert result.total_processed == 5
    assert "EMAIL-001" in result.skipped_email_ids
    assert "EMAIL-002" in result.skipped_email_ids


def test_processed_results_are_persisted(monkeypatch):

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        mock_classify_email
    )

    repository = FakeInboxRepository()

    result = run_inbox_triage_agent(
        repository=repository,
        **fake_agents(),
    )

    assert len(repository.completed) == 7
    assert "EMAIL-001" in repository.completed
    assert result.total_processed == 7


def test_failed_classification_is_recorded(monkeypatch):

    def failing_classifier(email, security_result):
        raise RuntimeError("Simulated classification failure")

    monkeypatch.setattr(
        "agents.inbox_triage.agent.classify_email",
        failing_classifier
    )

    repository = FakeInboxRepository()

    result = run_inbox_triage_agent(
        repository=repository
    )

    assert result.total_failed == 7
    assert result.total_processed == 0
    assert len(repository.failed) == 7

    assert all(
        item.stage == "classification"
        for item in result.failed_emails
    )


def test_agent_accepts_custom_empty_connector():

    class EmptyEmailConnector:

        def fetch_emails(self):
            return []

    repository = FakeInboxRepository()

    result = run_inbox_triage_agent(
        connector=EmptyEmailConnector(),
        repository=repository
    )

    assert result.total_fetched == 0
    assert result.total_processed == 0
    assert result.total_failed == 0
