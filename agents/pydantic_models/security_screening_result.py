
from typing import Literal
from pydantic import BaseModel, Field


class SecurityScreeningResult(BaseModel):

    email_id: str

    risk_level: Literal[
        "none",
        "medium",
        "high"
    ] = "none"

    is_suspicious: bool = False

    requires_human_review: bool = False

    security_flags: list[str] = Field(default_factory=list)

    screening_summary: str = ""
