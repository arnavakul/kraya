
from pydantic_models.email_message import EmailMessage
from pydantic_models.inbox_triage_result import InboxTriageResult

from tools.inbox.inbox_repository import InboxRepository


class FakeResult:

    def __init__(self, returned_id=None):
        self.returned_id = returned_id

    def scalar_one_or_none(self):
        return self.returned_id


class FakeSession:

    def __init__(self, returned_id=None):
        self.returned_id = returned_id
        self.executed_query = None
        self.executed_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def begin(self):
        return self

    def execute(self, query, params):
        self.executed_query = str(query)
        self.executed_params = params
        return FakeResult(self.returned_id)


def create_email():

    return EmailMessage(
        email_id="EMAIL-001",
        sender_email="supplier@example.com",
        subject="Quotation",
        body="Please find our quotation."
    )


def create_triage_result():

    return InboxTriageResult(
        email_id="EMAIL-001",
        category="quotation",
        confidence=0.95,
        summary="Supplier submitted quotation.",
        routing_action="quotation_processing"
    )


def create_repository(returned_id="EMAIL-001"):

    session = FakeSession(returned_id)

    def session_factory():
        return session

    return InboxRepository(session_factory), session


def test_claim_new_email():

    repository, session = create_repository()

    result = repository.claim_email(create_email())

    assert result is True
    assert session.executed_params["email_id"] == "EMAIL-001"
    assert "ON CONFLICT (email_id) DO NOTHING" in session.executed_query


def test_duplicate_email_not_claimed():

    repository, session = create_repository(returned_id=None)

    result = repository.claim_email(create_email())

    assert result is False


def test_complete_email():

    repository, session = create_repository()

    result = repository.complete_email(
        "EMAIL-001",
        create_triage_result()
    )

    assert result is True
    assert session.executed_params["category"] == "quotation"
    assert session.executed_params["routing_action"] == "quotation_processing"
    assert "processing_status = 'completed'" in session.executed_query


def test_complete_email_rejects_mismatched_id():

    repository, _ = create_repository()

    result = create_triage_result()

    result.email_id = "EMAIL-999"

    try:
        repository.complete_email("EMAIL-001", result)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "IDs do not match" in str(error)


def test_fail_email():

    repository, session = create_repository()

    result = repository.fail_email(
        "EMAIL-001",
        "Classification failed"
    )

    assert result is True
    assert session.executed_params["error_message"] == "Classification failed"
    assert "processing_status = 'failed'" in session.executed_query


def test_retry_failed_email():

    repository, session = create_repository()

    result = repository.retry_failed_email("EMAIL-001")

    assert result is True
    assert "processing_status = 'failed'" in session.executed_query
    assert "processing_status = 'processing'" in session.executed_query


def test_retry_nonexistent_or_non_failed_email():

    repository, _ = create_repository(returned_id=None)

    result = repository.retry_failed_email("EMAIL-001")

    assert result is False


def test_security_flags_are_serialized():

    repository, session = create_repository()

    triage_result = create_triage_result()
    triage_result.security_flags = ["prompt_injection"]

    repository.complete_email("EMAIL-001", triage_result)

    assert session.executed_params["security_flags"] == '["prompt_injection"]'
