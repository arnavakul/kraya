from pydantic import BaseModel
from datetime import datetime, date
from typing import List


class RFQ(BaseModel):
    rfq_id: int

    procurement_request_id: int

    supplier_ids: List[int]

    issue_date: datetime
    response_deadline: date

    status: str = "draft"