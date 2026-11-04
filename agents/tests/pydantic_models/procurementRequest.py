from pydantic import BaseModel
from datetime import date, datetime
from .requirement import Requirement

class ProcurementRequest(BaseModel):
    request_id: int

    requester_name: str
    department: str

    requirement: Requirement

    budget: float
    currency: str

    deadline: date

    priority: str = "medium"
    status: str = "draft"

    created_at: datetime