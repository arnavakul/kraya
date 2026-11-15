
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class EmailAttachment(BaseModel):
    filename: str
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class EmailMessage(BaseModel):
    """
    Normalized incoming supplier email.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    email_id: str = Field(min_length=1)
    sender_email: str = Field(min_length=3)
    sender_name: str | None = None

    subject: str = ""
    body: str = Field(min_length=1)

    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    thread_id: str | None = None
    in_reply_to: str | None = None

    attachments: list[EmailAttachment] = Field(
        default_factory=list
    )
