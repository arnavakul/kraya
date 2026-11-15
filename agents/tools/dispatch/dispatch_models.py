
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


DispatchStatus = Literal[
    "pending",
    "sending",
    "sent",
    "failed"
]

DeliveryStatus = Literal[
    "unknown",
    "delivered",
    "bounced"
]


class EmailMessage(BaseModel):
    rfq_id: UUID
    recipient_email: str
    subject: str
    body: str
    idempotency_key: str

    @field_validator("recipient_email")
    @classmethod
    def validate_recipient_email(cls, value: str) -> str:
        value = value.strip()

        if not value or "@" not in value:
            raise ValueError("A valid recipient email is required.")

        return value

    @field_validator("subject", "body", "idempotency_key")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be empty.")

        return value


class DispatchRecord(BaseModel):
    dispatch_id: UUID = Field(default_factory=uuid4)

    rfq_id: UUID
    recipient_email: str
    subject: str

    idempotency_key: str

    status: DispatchStatus = "pending"
    delivery_status: DeliveryStatus = "unknown"

    provider: str | None = None
    provider_message_id: str | None = None

    attempt_count: int = 0
    last_error: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    
    
class EmailSendResult(BaseModel):
    success: bool

    provider: str

    provider_message_id: str | None = None

    error: str | None = None

