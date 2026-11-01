from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SupplierResponse(BaseModel):
    response_id: int

    rfq_id: int
    supplier_id: int

    submitted_at: datetime

    status: str = "received"

    message: Optional[str] = None

    quote_id: Optional[int] = None