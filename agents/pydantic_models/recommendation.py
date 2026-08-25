from pydantic import BaseModel, Field
from typing import List, Optional


class Recommendation(BaseModel):
    recommendation_id: int

    procurement_request_id: int

    recommended_supplier_id: int

    recommended_quote_id: int

    reason: str

    advantages: List[str] = Field(default_factory=list)
    disadvantages: List[str] = Field(default_factory=list)

    confidence_score: float = Field(
        ge=0,
        le=1
    )

    estimated_savings: Optional[float] = None

    status: str = "pending"