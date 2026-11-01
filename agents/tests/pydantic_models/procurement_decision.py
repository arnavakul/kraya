from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProcurementDecision(BaseModel):
    decision_id: int

    procurement_request_id: int

    selected_supplier_id: Optional[int] = None
    selected_quote_id: Optional[int] = None

    decision: str

    justification: str

    final_amount: Optional[float] = None

    decided_by: str

    decided_at: datetime