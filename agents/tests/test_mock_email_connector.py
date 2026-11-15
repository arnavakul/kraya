
from tools.inbox.mock_email_connector import MockEmailConnector


def test_fetch_emails():

    connector = MockEmailConnector()

    emails = connector.fetch_emails()

    assert len(emails) == 7


def test_all_emails_are_valid():

    connector = MockEmailConnector()

    emails = connector.fetch_emails()

    for email in emails:
        assert email.email_id
        assert email.sender_email
        assert email.body


def test_email_ids_are_unique():

    connector = MockEmailConnector()

    emails = connector.fetch_emails()

    email_ids = [email.email_id for email in emails]

    assert len(email_ids) == len(set(email_ids))


def test_fetch_returns_separate_list():

    connector = MockEmailConnector()

    first = connector.fetch_emails()
    second = connector.fetch_emails()

    assert first is not second
