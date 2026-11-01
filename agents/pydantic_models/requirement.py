
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class Requirement(BaseModel):
    """
    Finalized procurement requirement.

    This is the object passed to downstream agents.
    """

    product_service: str

    quantity: float = Field(gt=0)

    specifications: Optional[str] = None

    quality_requirements: Optional[str] = None

    delivery_location: str

    delivery_deadline: Optional[date] = None

    budget: Optional[float] = Field(
        default=None,
        gt=0
    )

    currency: str = "INR"

    mandatory_constraints: List[str] = Field(
        default_factory=list
    )

    preferences: List[str] = Field(
        default_factory=list
    )
