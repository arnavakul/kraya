
from pydantic import BaseModel
from typing import Optional, List, Literal

from pydantic_models.requirement import Requirement


class IntakeResult(BaseModel):

    status: Literal[
        "needs_clarification",
        "validated",
        "failed"
    ]

    requirement: Optional[Requirement] = None

    missing_fields: List[str] = []

    clarification_questions: List[str] = []

    errors: List[str] = []
