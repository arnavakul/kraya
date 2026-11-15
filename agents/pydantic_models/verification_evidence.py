from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class VerificationEvidence(BaseModel):

    field: str

    value: Optional[str] = None

    source: str

    verification_status: Literal[
        "verified",
        "unverified",
        "inconsistent",
        "expired",
        "not_available"
    ]

    evidence_reference: Optional[str] = None

    checked_at: datetime

    notes: Optional[str] = None