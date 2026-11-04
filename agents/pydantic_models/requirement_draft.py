
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class RequirementDraft(BaseModel):
    """
    Intermediate requirement extracted by Gemini.

    Missing fields are allowed here.
    """

    product_service: Optional[str] = None

    quantity: Optional[float] = Field(
        default=None,
        gt=0
    )

    specifications: Optional[str] = None

    quality_requirements: Optional[str] = None

    delivery_location: Optional[str] = None

    delivery_deadline: Optional[date] = None

    budget: Optional[float] = Field(
        default=None,
        gt=0
    )

    currency: Optional[str] = None

    mandatory_constraints: List[str] = Field(
        default_factory=list
    )

    preferences: List[str] = Field(
        default_factory=list
    )
