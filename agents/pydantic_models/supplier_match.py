
from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID


class MatchCriterion(BaseModel):
    criterion: str
    required_value: str
    supplier_value: str | None = None

    status: Literal[
        "matched",
        "not_matched",
        "not_verifiable"
    ]

    explanation: str


class SupplierMatch(BaseModel):
    supplier_id: UUID
    supplier_name: str

    overall_status: Literal[
        "matched",
        "partially_matched",
        "not_matched",
        "insufficient_data"
    ]

    criteria: list[MatchCriterion] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )
