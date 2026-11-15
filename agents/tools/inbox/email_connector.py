
from typing import Protocol

from pydantic_models.email_message import EmailMessage


class EmailConnector(Protocol):

    def fetch_emails(self) -> list[EmailMessage]:
        """Fetch incoming supplier emails."""
        ...
