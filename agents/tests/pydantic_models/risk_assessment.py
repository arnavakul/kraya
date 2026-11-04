from pydantic import BaseModel, Field
from typing import List


class RiskAssessment(BaseModel):
    supplier_id: int

    overall_risk_score: float = Field(
        ge=0,
        le=100
    )

    financial_risk: float = Field(ge=0, le=100)
    delivery_risk: float = Field(ge=0, le=100)
    quality_risk: float = Field(ge=0, le=100)
    compliance_risk: float = Field(ge=0, le=100)

    risk_factors: List[str] = Field(default_factory=list)

    recommendation: str

    assessed_by: str = "ai_agent"