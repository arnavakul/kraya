
from pydantic_models.email_message import EmailMessage
from pydantic_models.email_classification import EmailClassification

from orchestration.inbox_triage_graph import inbox_triage_graph


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
        "repository": repository
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
        "repository": repository
    })

    assert "GRAPH-001" in repository.completed

    saved_result = repository.completed["GRAPH-001"]

    assert saved_result.category == "quotation"
    assert saved_result.routing_action == "quotation_processing"


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
