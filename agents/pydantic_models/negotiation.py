from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NegotiationRound(BaseModel):
    round_id: int

    procurement_request_id: int

    supplier_id: int
    quote_id: int

    round_number: int

    initiated_by: str

    request: str

    supplier_response: Optional[str] = None

    previous_price: Optional[float] = None
    negotiated_price: Optional[float] = None

    status: str = "open"

    created_at: datetime