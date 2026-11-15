
from typing import Protocol

from tools.dispatch.dispatch_models import (
    EmailMessage,
    EmailSendResult
)


class EmailProvider(Protocol):

    def send(self, message: EmailMessage) -> EmailSendResult:
        ...
