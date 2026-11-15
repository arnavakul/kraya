
from typing import Literal

from pydantic import BaseModel, Field


class EmailClassification(BaseModel):

    category: Literal[
        "quotation",
        "question",
        "rejection",
        "follow_up",
        "spam",
        "out_of_office",
        "suspicious"
    ]

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    summary: str

    classification_source: Literal[
        "llm",
        "security_rule"
    ]
