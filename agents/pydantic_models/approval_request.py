from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApprovalRequest(BaseModel):
    approval_id: int

    procurement_request_id: int

    requested_by: str

    approver: Optional[str] = None

    amount: float

    reason: str

    status: str = "pending"

    requested_at: datetime
    approved_at: Optional[datetime] = None