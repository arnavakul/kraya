
from uuid import uuid4

from tools.dispatch.dispatch_models import (
    EmailMessage,
    EmailSendResult
)


class MockEmailProvider:

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages = []

    def send(self, message: EmailMessage) -> EmailSendResult:

        if self.should_fail:
            return EmailSendResult(
                success=False,
                provider="mock",
                error="Simulated email delivery failure."
            )

        provider_message_id = f"mock-{uuid4()}"

        self.sent_messages.append({
            "recipient": message.recipient_email,
            "subject": message.subject,
            "provider_message_id": provider_message_id
        })

        return EmailSendResult(
            success=True,
            provider="mock",
            provider_message_id=provider_message_id
        )
